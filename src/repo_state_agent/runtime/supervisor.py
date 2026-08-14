from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from ..continuation import (
    ACTION_COMPLETE,
    ACTION_PAUSE,
    ACTION_ROTATE,
    decide_continuation,
)
from ..model import ActiveState
from ..parsing import parse_active
from ..prompts import render_prompt
from ..verify import verify_repository
from .adapter import AgentAdapter
from .config import RuntimeConfig
from .model import RuntimeSummary
from .store import RuntimeLock, RuntimeLockError, RuntimeStore, utc_now

STATUS_COMPLETE = "COMPLETE"
STATUS_PAUSED = "PAUSED"
STATUS_FAILED = "FAILED"
STATUS_LIMIT_REACHED = "LIMIT_REACHED"
STATUS_DRY_RUN = "DRY_RUN"


@dataclass(frozen=True)
class SupervisorOptions:
    dry_run: bool = False
    wait_on_pause: bool = False
    poll_seconds: float = 2.0
    max_transitions: int = 100
    max_turns_per_epoch: int = 6
    rotate_input_tokens: int = 60_000
    max_total_input_tokens: int = 5_000_000
    quiet: bool = False


@dataclass(frozen=True)
class SupervisorResult:
    status: str
    reason: str
    summary_path: Path | None
    run_id: str
    exit_code: int


GateResolver = Callable[[ActiveState], str | None]
RuntimeEventSink = Callable[[dict[str, Any]], None]


def options_from_config(
    config: RuntimeConfig, *, dry_run: bool = False, quiet: bool = False
) -> SupervisorOptions:
    return SupervisorOptions(
        dry_run=dry_run,
        wait_on_pause=config.wait_on_pause,
        poll_seconds=config.poll_seconds,
        max_transitions=config.max_transitions,
        max_turns_per_epoch=config.max_turns_per_epoch,
        rotate_input_tokens=config.rotate_input_tokens,
        max_total_input_tokens=config.max_total_input_tokens,
        quiet=quiet,
    )


def supervise(
    root: Path,
    adapter: AgentAdapter,
    options: SupervisorOptions,
    *,
    gate_resolver: GateResolver | None = None,
    event_sink: RuntimeEventSink | None = None,
) -> SupervisorResult:
    root = root.resolve()
    initial_verification = verify_repository(root)
    if not initial_verification.ok:
        _notify_event(
            event_sink,
            {
                "type": "repository_verification_failed",
                "errors": list(initial_verification.errors),
            },
        )
        return SupervisorResult(
            status=STATUS_FAILED,
            reason="REPOSITORY_VERIFICATION_FAILED: " + "; ".join(initial_verification.errors),
            summary_path=None,
            run_id="",
            exit_code=23,
        )

    initial_state = parse_active(root)
    run_id = f"rsaw-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    store = RuntimeStore(root, run_id)
    summary = RuntimeSummary(
        run_id=run_id,
        repository=str(root),
        adapter=adapter.name,
        started_at=utc_now(),
        workstream=initial_state.workstream_id,
        initial_task=initial_state.task_id,
        run_dir=str(store.run_dir.relative_to(root)),
    )
    store.save_summary(summary)
    _record_event(
        store,
        event_sink,
        {
            "type": "supervisor_started",
            "run_id": run_id,
            "repository": str(root),
            "workstream": initial_state.workstream_id,
            "task": initial_state.task_id,
            "epoch": initial_state.epoch_id,
            "role": initial_state.current_role,
            "rotate_input_tokens": options.rotate_input_tokens,
            "max_turns_per_epoch": options.max_turns_per_epoch,
            "max_transitions": options.max_transitions,
        },
    )

    def finish(
        state: ActiveState,
        status: str,
        reason: str,
        exit_code: int,
    ) -> SupervisorResult:
        return _finish(
            summary,
            store,
            state,
            status,
            reason,
            exit_code,
            event_sink=event_sink,
        )

    if options.dry_run:
        decision = decide_continuation(initial_state)
        summary.status = STATUS_DRY_RUN
        summary.reason = ",".join(decision.reasons)
        summary.final_task = initial_state.task_id
        summary.count_transition(decision.action)
        summary.ended_at = utc_now()
        _record_event(
            store,
            event_sink,
            {
                "type": "dry_run",
                "action": decision.action,
                "reasons": list(decision.reasons),
            },
        )
        store.save_summary(summary)
        return SupervisorResult(STATUS_DRY_RUN, summary.reason, store.summary_path, run_id, 0)

    doctor_checked = False
    thread_id: str | None = None
    thread_turns = 0
    force_rotate_reason = ""
    last_active_signature = _active_signature(root)
    transition_count = 0

    try:
        with RuntimeLock.for_root(root):
            while transition_count < options.max_transitions:
                state = parse_active(root)
                decision = decide_continuation(state)
                summary.count_transition(decision.action)
                _record_event(
                    store,
                    event_sink,
                    {
                        "type": "transition",
                        "action": decision.action,
                        "reasons": list(decision.reasons),
                        "declared_decision": decision.declared_decision,
                        "task": state.task_id,
                        "epoch": state.epoch_id,
                        "role": state.current_role,
                        "human_gate": state.human_gate or None,
                    },
                )

                if decision.action == ACTION_COMPLETE:
                    return finish(
                        state,
                        STATUS_COMPLETE,
                        "WORKSTREAM_COMPLETE",
                        0,
                    )

                if decision.action == ACTION_PAUSE:
                    response = gate_resolver(state) if gate_resolver else None
                    if response:
                        doctor_failure = _check_adapter_once(
                            adapter,
                            store,
                            summary,
                            doctor_checked,
                            event_sink=event_sink,
                        )
                        doctor_checked = True
                        if doctor_failure:
                            return doctor_failure
                        result = _run_gate_resolution(
                            root=root,
                            state=state,
                            response=response,
                            adapter=adapter,
                            store=store,
                            summary=summary,
                            event_sink=event_sink,
                        )
                        if not result.ok:
                            return finish(
                                state,
                                STATUS_FAILED,
                                f"GATE_RESOLUTION_AGENT_FAILED: {result.error or result.exit_code}",
                                22,
                            )
                        _record_event(
                            store,
                            event_sink,
                            {"type": "repository_verification_started", "scope": "gate"},
                        )
                        verification = verify_repository(root)
                        if not verification.ok:
                            return finish(
                                state,
                                STATUS_FAILED,
                                "GATE_RESOLUTION_STATE_INVALID: "
                                + "; ".join(verification.errors),
                                23,
                            )
                        _record_event(
                            store,
                            event_sink,
                            {"type": "repository_verification_passed", "scope": "gate"},
                        )
                        if _active_signature(root) == last_active_signature:
                            return finish(
                                state,
                                STATUS_FAILED,
                                "GATE_RESOLUTION_DID_NOT_ADVANCE_STATE",
                                21,
                            )
                        last_active_signature = _active_signature(root)
                        summary.checkpoints_observed += 1
                        _record_event(
                            store,
                            event_sink,
                            {
                                "type": "checkpoint_observed",
                                "checkpoint": summary.checkpoints_observed,
                                "task": state.task_id,
                                "scope": "gate",
                            },
                        )
                        thread_id = None
                        thread_turns = 0
                        force_rotate_reason = "HUMAN_GATE_BOUNDARY"
                        transition_count += 1
                        continue

                    if options.wait_on_pause:
                        changed = _wait_for_state_change(
                            root, last_active_signature, options.poll_seconds
                        )
                        if not changed:
                            return finish(
                                state,
                                STATUS_PAUSED,
                                "PAUSE_INTERRUPTED",
                                20,
                            )
                        last_active_signature = _active_signature(root)
                        thread_id = None
                        thread_turns = 0
                        force_rotate_reason = "PAUSE_RESOLVED"
                        transition_count += 1
                        continue

                    summary.human_gate = state.human_gate
                    return finish(
                        state,
                        STATUS_PAUSED,
                        ",".join(decision.reasons),
                        20,
                    )

                fresh = (
                    decision.action == ACTION_ROTATE
                    or thread_id is None
                    or bool(force_rotate_reason)
                )
                if fresh:
                    thread_id = None
                    thread_turns = 0
                    summary.runtime_epochs += 1
                    summary.fresh_turns += 1
                    mode = "fresh"
                    rotate_reason = force_rotate_reason or ",".join(decision.reasons)
                    _record_event(
                        store,
                        event_sink,
                        {
                            "type": "runtime_epoch_started",
                            "runtime_epoch": summary.runtime_epochs,
                            "reason": rotate_reason,
                            "declared_epoch": state.epoch_id,
                            "role": state.current_role or state.next_role,
                        },
                    )
                    force_rotate_reason = ""
                else:
                    summary.resumed_turns += 1
                    mode = "continue"

                doctor_failure = _check_adapter_once(
                    adapter,
                    store,
                    summary,
                    doctor_checked,
                    event_sink=event_sink,
                )
                doctor_checked = True
                if doctor_failure:
                    return doctor_failure

                prompt = _supervised_prompt(root, mode)
                before_signature = _active_signature(root)
                summary.agent_turns += 1
                thread_turns += 1
                environment = {
                    "RSAW_SUPERVISED": "1",
                    "RSAW_RUN_ID": run_id,
                    "RSAW_RUNTIME_EPOCH": str(summary.runtime_epochs),
                    "RSAW_TASK_ID": state.task_id,
                    "RSAW_ROLE": state.current_role or state.next_role,
                }
                _record_event(
                    store,
                    event_sink,
                    {
                        "type": "agent_turn_started",
                        "turn": summary.agent_turns,
                        "runtime_epoch": summary.runtime_epochs,
                        "mode": mode,
                        "fresh": fresh,
                        "task": state.task_id,
                        "role": state.current_role or state.next_role,
                    },
                )
                result = adapter.run_turn(
                    prompt=prompt,
                    root=root,
                    run_dir=store.run_dir,
                    turn_index=summary.agent_turns,
                    thread_id=thread_id,
                    environment=environment,
                )
                summary.total_usage = summary.total_usage + result.usage
                summary.latest_thread_id = result.thread_id
                summary.last_event_path = (
                    str(result.events_path.relative_to(root)) if result.events_path else ""
                )
                summary.last_message_path = (
                    str(result.last_message_path.relative_to(root))
                    if result.last_message_path
                    else ""
                )
                _record_event(
                    store,
                    event_sink,
                    {
                        "type": "agent_turn_terminal",
                        "ok": result.ok,
                        "exit_code": result.exit_code,
                        "thread_id": result.thread_id,
                        "fresh": fresh,
                        "usage": result.usage.to_dict(),
                        "latest_turn_usage": result.latest_turn_usage.to_dict(),
                        "event_count": result.event_count,
                        "error": result.error or None,
                    },
                )
                store.save_summary(summary)

                if not result.ok:
                    return finish(
                        state,
                        STATUS_FAILED,
                        f"AGENT_TURN_FAILED: {result.error or result.exit_code}",
                        22,
                    )

                _record_event(
                    store,
                    event_sink,
                    {"type": "repository_verification_started", "scope": "checkpoint"},
                )
                verification = verify_repository(root)
                if not verification.ok:
                    return finish(
                        state,
                        STATUS_FAILED,
                        "REPOSITORY_STATE_INVALID: " + "; ".join(verification.errors),
                        23,
                    )
                _record_event(
                    store,
                    event_sink,
                    {"type": "repository_verification_passed", "scope": "checkpoint"},
                )

                after_signature = _active_signature(root)
                if after_signature == before_signature:
                    return finish(
                        state,
                        STATUS_FAILED,
                        "ACTIVE_STATE_NOT_ADVANCED",
                        21,
                    )
                summary.checkpoints_observed += 1
                last_active_signature = after_signature
                thread_id = result.thread_id
                transition_count += 1
                _record_event(
                    store,
                    event_sink,
                    {
                        "type": "checkpoint_observed",
                        "checkpoint": summary.checkpoints_observed,
                        "task": state.task_id,
                        "next_task": parse_active(root).task_id,
                    },
                )
                store.save_summary(summary)

                if (
                    options.max_total_input_tokens
                    and summary.total_usage.input_tokens >= options.max_total_input_tokens
                ):
                    return finish(
                        parse_active(root),
                        STATUS_LIMIT_REACHED,
                        "MAX_TOTAL_INPUT_TOKENS",
                        24,
                    )
                if thread_turns >= options.max_turns_per_epoch:
                    force_rotate_reason = "MAX_TURNS_PER_RUNTIME_EPOCH"
                    _record_event(
                        store,
                        event_sink,
                        {
                            "type": "rotation_scheduled",
                            "reason": force_rotate_reason,
                        },
                    )
                elif (
                    options.rotate_input_tokens
                    and result.latest_turn_usage.input_tokens >= options.rotate_input_tokens
                ):
                    force_rotate_reason = "TURN_INPUT_TOKEN_PRESSURE"
                    _record_event(
                        store,
                        event_sink,
                        {
                            "type": "rotation_scheduled",
                            "reason": force_rotate_reason,
                        },
                    )

            return finish(
                parse_active(root),
                STATUS_LIMIT_REACHED,
                "MAX_TRANSITIONS",
                24,
            )
    except RuntimeLockError as exc:
        return finish(
            _safe_state(root, initial_state),
            STATUS_FAILED,
            f"SUPERVISOR_LOCKED: {exc}",
            25,
        )
    except KeyboardInterrupt:
        return finish(
            _safe_state(root, initial_state),
            STATUS_PAUSED,
            "SUPERVISOR_INTERRUPTED",
            20,
        )
    except Exception as exc:  # pragma: no cover - final fail-closed boundary
        return finish(
            _safe_state(root, initial_state),
            STATUS_FAILED,
            f"SUPERVISOR_EXCEPTION: {type(exc).__name__}: {exc}",
            26,
        )


def _check_adapter_once(
    adapter: AgentAdapter,
    store: RuntimeStore,
    summary: RuntimeSummary,
    already_checked: bool,
    *,
    event_sink: RuntimeEventSink | None = None,
) -> SupervisorResult | None:
    if already_checked:
        return None
    doctor = adapter.doctor()
    _record_event(store, event_sink, {"type": "adapter_doctor", **doctor.to_dict()})
    if doctor.ok:
        return None
    summary.status = STATUS_FAILED
    summary.reason = "ADAPTER_DOCTOR_FAILED: " + "; ".join(doctor.errors)
    summary.ended_at = utc_now()
    store.save_summary(summary)
    _notify_event(
        event_sink,
        {
            "type": "supervisor_terminal",
            "status": STATUS_FAILED,
            "reason": summary.reason,
        },
    )
    return SupervisorResult(
        STATUS_FAILED, summary.reason, store.summary_path, summary.run_id, 22
    )


def _run_gate_resolution(
    *,
    root: Path,
    state: ActiveState,
    response: str,
    adapter: AgentAdapter,
    store: RuntimeStore,
    summary: RuntimeSummary,
    event_sink: RuntimeEventSink | None = None,
):
    summary.runtime_epochs += 1
    summary.agent_turns += 1
    summary.fresh_turns += 1
    response_hash = hashlib.sha256(response.encode("utf-8")).hexdigest()
    _record_event(
        store,
        event_sink,
        {
            "type": "human_gate_response",
            "gate": state.human_gate,
            "response_sha256": response_hash,
        },
    )
    base = render_prompt(root, role=None, mode="fresh")
    instruction = f"""

RSAW HUMAN-GATE RESOLUTION TURN

The human supplied this exact response to the active gate:
{json.dumps(response)}

Apply the response only through the repository's existing governance and safety
mechanisms. Verify all authoritative bindings. Resolve or reject the gate,
persist evidence, update ACTIVE.md, and set the next transition. Do not execute
the next role or task in this turn. Do not print a prompt for human relay; the
RSAW supervisor will rotate automatically.
"""
    _record_event(
        store,
        event_sink,
        {
            "type": "agent_turn_started",
            "turn": summary.agent_turns,
            "runtime_epoch": summary.runtime_epochs,
            "mode": "fresh",
            "fresh": True,
            "task": state.task_id,
            "role": "GateResolver",
        },
    )
    result = adapter.run_turn(
        prompt=base + instruction,
        root=root,
        run_dir=store.run_dir,
        turn_index=summary.agent_turns,
        thread_id=None,
        environment={
            "RSAW_SUPERVISED": "1",
            "RSAW_GATE_RESOLUTION": "1",
            "RSAW_RUN_ID": summary.run_id,
            "RSAW_TASK_ID": state.task_id,
        },
    )
    summary.total_usage = summary.total_usage + result.usage
    summary.latest_thread_id = result.thread_id
    summary.last_event_path = (
        str(result.events_path.relative_to(root)) if result.events_path else ""
    )
    summary.last_message_path = (
        str(result.last_message_path.relative_to(root))
        if result.last_message_path
        else ""
    )
    _record_event(
        store,
        event_sink,
        {
            "type": "gate_resolution_turn_terminal",
            "ok": result.ok,
            "exit_code": result.exit_code,
            "usage": result.usage.to_dict(),
            "latest_turn_usage": result.latest_turn_usage.to_dict(),
            "error": result.error or None,
        },
    )
    store.save_summary(summary)
    return result


def _supervised_prompt(root: Path, mode: str) -> str:
    return render_prompt(root, role=None, mode=mode) + """

RSAW RUNTIME SUPERVISOR IS ACTIVE

Complete exactly one durable repository checkpoint in this turn. Do not ask the
human to copy or relay a next prompt. Do not spawn a replacement model context.
Update ACTIVE.md with the next task and transition. The supervisor will reuse,
rotate, pause, or complete the workstream after verifying repository state.
If human or external action is required, record a Human Gate and PAUSE/STOP
metadata rather than busy-waiting or bypassing authority.
"""


def _active_signature(root: Path) -> str:
    active = root / "ACTIVE.md"
    return hashlib.sha256(active.read_bytes()).hexdigest()


def _safe_state(root: Path, fallback: ActiveState) -> ActiveState:
    try:
        return parse_active(root)
    except Exception:
        return fallback


def _wait_for_state_change(root: Path, previous: str, poll_seconds: float) -> bool:
    try:
        while True:
            time.sleep(poll_seconds)
            if _active_signature(root) != previous:
                return True
    except KeyboardInterrupt:
        return False


def _finish(
    summary: RuntimeSummary,
    store: RuntimeStore,
    state: ActiveState,
    status: str,
    reason: str,
    exit_code: int,
    *,
    event_sink: RuntimeEventSink | None = None,
) -> SupervisorResult:
    summary.status = status
    summary.reason = reason
    summary.final_task = state.task_id
    summary.human_gate = state.human_gate
    summary.ended_at = utc_now()
    _record_event(
        store,
        event_sink,
        {
            "type": "supervisor_terminal",
            "status": status,
            "reason": reason,
            "final_task": state.task_id,
            "human_gate": state.human_gate or None,
        },
    )
    store.save_summary(summary)
    return SupervisorResult(status, reason, store.summary_path, summary.run_id, exit_code)


def _record_event(
    store: RuntimeStore,
    event_sink: RuntimeEventSink | None,
    event: dict[str, Any],
) -> None:
    store.append_event(event)
    _notify_event(event_sink, event)


def _notify_event(
    event_sink: RuntimeEventSink | None,
    event: dict[str, Any],
) -> None:
    if event_sink is None:
        return
    try:
        event_sink(event)
    except Exception:
        # The presentation layer is never allowed to alter lifecycle semantics.
        return
