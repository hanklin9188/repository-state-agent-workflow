from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from repo_state_agent.runtime.model import (
    AdapterDoctorResult,
    AgentTurnResult,
    TokenUsage,
)
from repo_state_agent.runtime.supervisor import SupervisorOptions, supervise


@dataclass
class Step:
    continuation: str
    task_id: str
    next_task_id: str
    current_role: str = "Builder"
    next_role: str = "Builder"
    human_gate: str = "None."


def _write_repo(
    root: Path,
    *,
    continuation: str = "ROTATE_REQUIRED",
    human_gate: str = "None.",
    current_role: str = "Builder",
    next_role: str = "Builder",
    task_id: str = "T-1",
    next_task_id: str = "T-2",
) -> None:
    (root / "docs/tasks").mkdir(parents=True, exist_ok=True)
    (root / "docs/workstreams").mkdir(parents=True, exist_ok=True)
    (root / "AGENTS.md").write_text("# Policy\n", encoding="utf-8")
    (root / "docs/workstreams/W-1.md").write_text("# Workstream\n", encoding="utf-8")
    (root / f"docs/tasks/{task_id}.md").write_text("# Task\n", encoding="utf-8")
    (root / f"docs/tasks/{next_task_id}.md").write_text("# Next\n", encoding="utf-8")
    (root / "ACTIVE.md").write_text(
        f"""# Active Handoff

## Workstream
ID: W-1
Spec: docs/workstreams/W-1.md

## Context Epoch
ID: E-1
Role: {current_role}

## Active Task
ID: {task_id}
Spec: docs/tasks/{task_id}.md

## Required Reads
- AGENTS.md
- ACTIVE.md
- docs/tasks/{task_id}.md

## Human Gate
{human_gate}

## Next Exact Action
Do the task.

## Stop Condition
Checkpoint is written.

## Continuation Gate
Decision: {continuation}
Reason: test

## Next Task
ID: {next_task_id}
Spec: docs/tasks/{next_task_id}.md

## Next Session Role
{next_role}

## Recommended Reasoning
Medium
""",
        encoding="utf-8",
    )


class FakeAdapter:
    name = "fake"

    def __init__(self, root: Path, steps: list[Step], *, fail_at: int | None = None) -> None:
        self.root = root
        self.steps = steps
        self.calls: list[str | None] = []
        self.fail_at = fail_at

    def doctor(self) -> AdapterDoctorResult:
        return AdapterDoctorResult(True, "fake", "fake", "1")

    def run_turn(self, *, thread_id: str | None, turn_index: int, **_: object) -> AgentTurnResult:
        self.calls.append(thread_id)
        if self.fail_at == turn_index:
            return AgentTurnResult(exit_code=1, thread_id=thread_id, error="boom")
        step = self.steps[turn_index - 1]
        _write_repo(
            self.root,
            continuation=step.continuation,
            human_gate=step.human_gate,
            current_role=step.current_role,
            next_role=step.next_role,
            task_id=step.task_id,
            next_task_id=step.next_task_id,
        )
        return AgentTurnResult(
            exit_code=0,
            thread_id=thread_id or f"thread-{turn_index}",
            usage=TokenUsage(input_tokens=100),
            latest_turn_usage=TokenUsage(input_tokens=100),
        )


class DoctorFailAdapter(FakeAdapter):
    def doctor(self) -> AdapterDoctorResult:
        raise AssertionError("doctor should not run while paused")


def _options() -> SupervisorOptions:
    return SupervisorOptions(
        max_transitions=10,
        max_turns_per_epoch=5,
        rotate_input_tokens=1000,
        max_total_input_tokens=10000,
        quiet=True,
    )


def test_supervisor_continues_then_rotates_automatically(tmp_path: Path) -> None:
    _write_repo(tmp_path, continuation="ROTATE_REQUIRED")
    adapter = FakeAdapter(
        tmp_path,
        [
            Step("CONTINUE_ALLOWED", "T-2", "T-3"),
            Step("ROTATE_REQUIRED", "T-3", "T-4", next_role="Analyst"),
            Step("COMPLETE", "T-4", "T-5", current_role="Analyst", next_role="Analyst"),
        ],
    )
    result = supervise(tmp_path, adapter, _options())
    assert result.status == "COMPLETE"
    assert adapter.calls == [None, "thread-1", None]


def test_supervisor_pauses_without_launching_at_human_gate(tmp_path: Path) -> None:
    _write_repo(tmp_path, continuation="STOP_REQUIRED", human_gate="APPROVAL")
    adapter = DoctorFailAdapter(tmp_path, [])
    result = supervise(tmp_path, adapter, _options())
    assert result.status == "PAUSED"
    assert result.exit_code == 20
    assert adapter.calls == []


def test_interactive_gate_resolution_then_rotation(tmp_path: Path) -> None:
    _write_repo(tmp_path, continuation="STOP_REQUIRED", human_gate="APPROVAL")
    adapter = FakeAdapter(
        tmp_path,
        [
            Step("ROTATE_REQUIRED", "T-2", "T-3", next_role="Runner"),
            Step("COMPLETE", "T-3", "T-4", current_role="Runner", next_role="Runner"),
        ],
    )
    responses = iter(["APPROVE"])
    result = supervise(tmp_path, adapter, _options(), gate_resolver=lambda _: next(responses))
    assert result.status == "COMPLETE"
    assert adapter.calls == [None, None]


def test_supervisor_does_not_retry_agent_failure(tmp_path: Path) -> None:
    _write_repo(tmp_path, continuation="ROTATE_REQUIRED")
    adapter = FakeAdapter(tmp_path, [Step("COMPLETE", "T-2", "T-3")], fail_at=1)
    result = supervise(tmp_path, adapter, _options())
    assert result.status == "FAILED"
    assert len(adapter.calls) == 1


def test_supervisor_forces_rotation_on_input_pressure(tmp_path: Path) -> None:
    _write_repo(tmp_path, continuation="ROTATE_REQUIRED")
    adapter = FakeAdapter(
        tmp_path,
        [
            Step("CONTINUE_ALLOWED", "T-2", "T-3"),
            Step("COMPLETE", "T-3", "T-4"),
        ],
    )
    pressured = SupervisorOptions(
        max_transitions=5,
        max_turns_per_epoch=10,
        rotate_input_tokens=50,
        max_total_input_tokens=10000,
        quiet=True,
    )
    result = supervise(tmp_path, adapter, pressured)
    assert result.status == "COMPLETE"
    assert adapter.calls == [None, None]


def test_dry_run_never_calls_adapter(tmp_path: Path) -> None:
    _write_repo(tmp_path)
    adapter = DoctorFailAdapter(tmp_path, [])
    result = supervise(tmp_path, adapter, SupervisorOptions(dry_run=True))
    assert result.status == "DRY_RUN"
