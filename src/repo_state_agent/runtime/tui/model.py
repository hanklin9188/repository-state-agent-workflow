from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from time import monotonic
from typing import Any

from ...model import ActiveState
from ...parsing import parse_active
from ..model import TokenUsage

_MAX_RECENT_EVENTS = 5
_REASONING_TYPES = {"analysis", "reasoning", "reasoning_summary"}
_COMMAND_TYPES = {"command", "command_execution", "shell", "shell_command"}
_FILE_TYPES = {"file_change", "file_edit", "file_read", "read_file", "write_file"}
_TOOL_TYPES = {"mcp_tool_call", "tool_call", "function_call"}


@dataclass(frozen=True)
class Activity:
    kind: str
    title: str
    detail: str = ""


@dataclass(frozen=True)
class RecentEvent:
    kind: str
    title: str
    detail: str = ""
    level: str = "info"


@dataclass(frozen=True)
class DashboardSnapshot:
    project: str
    workstream_id: str
    workstream_title: str
    run_id: str
    status: str
    reason: str
    role: str
    declared_epoch: str
    runtime_epoch: int
    task_id: str
    task_title: str
    next_task_id: str
    next_task_title: str
    next_action: str
    next_reason: str
    checkpoints_observed: int
    agent_turns: int
    stages: tuple[str, ...]
    current_stage: int | None
    current_activity: Activity
    recent_events: tuple[RecentEvent, ...]
    latest_usage: TokenUsage
    total_usage: TokenUsage
    rotate_input_tokens: int
    human_gate: str
    started_monotonic: float
    last_durable_monotonic: float | None
    transition_started: float | None
    transition_from_role: str
    transition_from_epoch: str
    transition_to_role: str
    transition_to_epoch: str
    transition_reason: str
    summary_path: str

    @property
    def fresh_input_tokens(self) -> int:
        return max(0, self.latest_usage.input_tokens - self.latest_usage.cached_input_tokens)

    @property
    def cache_ratio(self) -> float | None:
        if self.latest_usage.input_tokens <= 0:
            return None
        return min(
            1.0,
            max(0.0, self.latest_usage.cached_input_tokens / self.latest_usage.input_tokens),
        )

    @property
    def context_pressure(self) -> float | None:
        if self.rotate_input_tokens <= 0 or self.latest_usage.input_tokens <= 0:
            return None
        return min(1.25, self.latest_usage.input_tokens / self.rotate_input_tokens)


class DashboardModel:
    """Thread-safe presentation state derived from repository and runtime events.

    This model is intentionally downstream from the supervisor. It may observe
    lifecycle decisions, but it never makes or mutates them.
    """

    def __init__(self, root: Path, *, rotate_input_tokens: int) -> None:
        self.root = root.resolve()
        self.rotate_input_tokens = rotate_input_tokens
        self._lock = RLock()
        self._project = _display_name(self.root.name)
        self._workstream_id = ""
        self._workstream_title = ""
        self._run_id = ""
        self._status = "STARTING"
        self._reason = ""
        self._role = ""
        self._declared_epoch = ""
        self._runtime_epoch = 0
        self._task_id = ""
        self._task_title = ""
        self._next_task_id = ""
        self._next_task_title = ""
        self._next_action = "—"
        self._next_reason = ""
        self._checkpoints_observed = 0
        self._agent_turns = 0
        self._stages: tuple[str, ...] = ()
        self._current_stage: int | None = None
        self._current_activity = Activity("startup", "Preparing RSAW supervisor")
        self._recent_events: deque[RecentEvent] = deque(maxlen=_MAX_RECENT_EVENTS)
        self._latest_usage = TokenUsage()
        self._total_usage = TokenUsage()
        self._human_gate = ""
        self._started_monotonic = monotonic()
        self._last_durable_monotonic: float | None = None
        self._transition_started: float | None = None
        self._transition_from_role = ""
        self._transition_from_epoch = ""
        self._transition_to_role = ""
        self._transition_to_epoch = ""
        self._transition_reason = ""
        self._summary_path = ""
        self.refresh_repository_state()

    def refresh_repository_state(self) -> None:
        try:
            state = parse_active(self.root)
        except (OSError, ValueError):
            return
        with self._lock:
            self._apply_active_state(state)

    def handle_supervisor_event(self, event: dict[str, Any]) -> None:
        event_type = str(event.get("type") or "")
        now = monotonic()
        with self._lock:
            if event_type == "supervisor_started":
                self._run_id = _string(event.get("run_id"))
                self._status = "STARTING"
                self._current_activity = Activity(
                    "startup", "Verifying repository authority", "AGENTS.md · ACTIVE.md"
                )
                threshold = _integer(event.get("rotate_input_tokens"))
                if threshold >= 0:
                    self.rotate_input_tokens = threshold
                self._refresh_repository_state_locked()
                return

            if event_type == "adapter_doctor":
                ok = bool(event.get("ok"))
                self._status = "STARTING" if ok else "FAILED"
                self._current_activity = Activity(
                    "adapter",
                    "Codex runtime ready" if ok else "Codex runtime check failed",
                    _string(event.get("version")),
                )
                if not ok:
                    self._reason = _join_strings(event.get("errors"))
                    self._push_recent("error", "Codex adapter check failed", self._reason, "error")
                return

            if event_type == "transition":
                self._refresh_repository_state_locked()
                action = _string(event.get("action")) or "—"
                reasons = _join_strings(event.get("reasons"))
                self._next_action = action
                self._next_reason = reasons
                human_gate = _string(event.get("human_gate"))
                if human_gate:
                    self._human_gate = human_gate
                if action == "ROTATE":
                    self._status = "ROTATING" if self._runtime_epoch else "STARTING"
                    self._transition_started = now
                    self._transition_from_role = self._role
                    self._transition_from_epoch = self._declared_epoch
                    self._transition_to_role = self._next_role_from_repository()
                    self._transition_to_epoch = "fresh"
                    self._transition_reason = reasons
                    self._current_activity = Activity(
                        "rotate", "Preparing a fresh Codex context", reasons
                    )
                    if self._runtime_epoch:
                        self._push_recent("rotate", "Context rotation scheduled", reasons)
                elif action == "PAUSE":
                    self._status = "PAUSED"
                    self._current_activity = Activity(
                        "pause", "Waiting for operator action", self._human_gate or reasons
                    )
                elif action == "COMPLETE":
                    self._status = "COMPLETE"
                    self._current_activity = Activity(
                        "complete", "Workstream complete", self._task_title
                    )
                else:
                    self._status = "WORKING"
                return

            if event_type == "runtime_epoch_started":
                self._runtime_epoch = max(
                    self._runtime_epoch, _integer(event.get("runtime_epoch"))
                )
                self._status = "WORKING"
                self._transition_to_role = self._role
                self._transition_to_epoch = str(self._runtime_epoch)
                reason = _string(event.get("reason"))
                if self._runtime_epoch > 1:
                    self._push_recent(
                        "epoch", f"Fresh context · epoch {self._runtime_epoch}", reason
                    )
                return

            if event_type == "agent_turn_started":
                self._agent_turns = max(self._agent_turns, _integer(event.get("turn")))
                self._status = "WORKING"
                mode = _string(event.get("mode"))
                title = (
                    "Starting fresh Codex context"
                    if mode == "fresh"
                    else "Continuing current Codex context"
                )
                self._current_activity = Activity("agent", title, self._task_title)
                return

            if event_type == "repository_verification_started":
                self._status = "VALIDATING"
                self._current_activity = Activity(
                    "validate", "Verifying durable repository state", "ACTIVE.md · references"
                )
                return

            if event_type == "repository_verification_passed":
                self._status = "CHECKPOINTING"
                self._current_activity = Activity(
                    "checkpoint", "Repository checkpoint verified", self._task_title
                )
                return

            if event_type == "checkpoint_observed":
                self._checkpoints_observed = max(
                    self._checkpoints_observed, _integer(event.get("checkpoint"))
                )
                self._last_durable_monotonic = now
                self._status = "CHECKPOINTING"
                self._refresh_repository_state_locked()
                self._push_recent(
                    "checkpoint",
                    f"Checkpoint {self._checkpoints_observed} accepted",
                    self._task_title,
                    "success",
                )
                return

            if event_type in {"agent_turn_terminal", "gate_resolution_turn_terminal"}:
                latest = _usage(event.get("latest_turn_usage") or event.get("usage"))
                total = _usage(event.get("usage"))
                if latest.input_tokens or latest.output_tokens:
                    self._latest_usage = latest
                if total.input_tokens or total.output_tokens:
                    # agent_turn_terminal usage is per turn; the summary remains authoritative.
                    self._total_usage = self._total_usage + total
                if not bool(event.get("ok", True)):
                    self._status = "FAILED"
                    self._reason = _string(event.get("error")) or "Agent turn failed"
                    self._current_activity = Activity("error", "Agent turn failed", self._reason)
                    self._push_recent("error", "Agent turn failed", self._reason, "error")
                return

            if event_type == "human_gate_response":
                self._status = "WORKING"
                self._push_recent("gate", "Human gate response recorded", self._human_gate)
                return

            if event_type == "supervisor_terminal":
                self._status = _string(event.get("status")) or self._status
                self._reason = _string(event.get("reason"))
                gate = _string(event.get("human_gate"))
                if gate:
                    self._human_gate = gate
                self._set_terminal_activity()

    def handle_codex_event(self, event: dict[str, Any]) -> None:
        event_type = str(event.get("type") or "")
        with self._lock:
            if event_type == "thread.started":
                self._status = "WORKING"
                self._current_activity = Activity(
                    "thread", "Codex context is ready", self._task_title
                )
                return

            if event_type == "turn.completed":
                usage = _usage(event.get("usage"))
                self._latest_usage = usage
                self._current_activity = Activity(
                    "turn", "Codex turn completed", _usage_detail(usage)
                )
                self._push_recent("turn", "Codex turn completed", _usage_detail(usage), "success")
                return

            if event_type in {"turn.failed", "error"}:
                message = _error_text(event)
                self._status = "FAILED"
                self._reason = message
                self._current_activity = Activity("error", "Codex reported an error", message)
                self._push_recent("error", "Codex reported an error", message, "error")
                return

            if event_type == "codex.diagnostic":
                message = _string(event.get("message"))
                if message:
                    self._current_activity = Activity("diagnostic", "Codex diagnostic", message)
                return

            activity = _activity_from_codex_event(event)
            if activity is None:
                return
            self._current_activity = activity
            if event_type.endswith(".completed"):
                level = "success" if activity.kind in {"command", "edit", "tool"} else "info"
                self._push_recent(activity.kind, activity.title, activity.detail, level)

    def finalize(
        self,
        *,
        status: str,
        reason: str,
        summary_path: str = "",
        summary: dict[str, Any] | None = None,
    ) -> None:
        with self._lock:
            self._status = status
            self._reason = reason
            self._summary_path = summary_path
            if summary:
                self._runtime_epoch = _integer(summary.get("runtime_epochs"))
                self._agent_turns = _integer(summary.get("agent_turns"))
                self._checkpoints_observed = _integer(summary.get("checkpoints_observed"))
                self._total_usage = _usage(summary.get("total_usage"))
                gate = _string(summary.get("human_gate"))
                if gate:
                    self._human_gate = gate
            self._refresh_repository_state_locked()
            self._set_terminal_activity()

    def snapshot(self) -> DashboardSnapshot:
        with self._lock:
            return DashboardSnapshot(
                project=self._project,
                workstream_id=self._workstream_id,
                workstream_title=self._workstream_title,
                run_id=self._run_id,
                status=self._status,
                reason=self._reason,
                role=self._role,
                declared_epoch=self._declared_epoch,
                runtime_epoch=self._runtime_epoch,
                task_id=self._task_id,
                task_title=self._task_title,
                next_task_id=self._next_task_id,
                next_task_title=self._next_task_title,
                next_action=self._next_action,
                next_reason=self._next_reason,
                checkpoints_observed=self._checkpoints_observed,
                agent_turns=self._agent_turns,
                stages=self._stages,
                current_stage=self._current_stage,
                current_activity=self._current_activity,
                recent_events=tuple(self._recent_events),
                latest_usage=self._latest_usage,
                total_usage=self._total_usage,
                rotate_input_tokens=self.rotate_input_tokens,
                human_gate=self._human_gate,
                started_monotonic=self._started_monotonic,
                last_durable_monotonic=self._last_durable_monotonic,
                transition_started=self._transition_started,
                transition_from_role=self._transition_from_role,
                transition_from_epoch=self._transition_from_epoch,
                transition_to_role=self._transition_to_role,
                transition_to_epoch=self._transition_to_epoch,
                transition_reason=self._transition_reason,
                summary_path=self._summary_path,
            )

    def _apply_active_state(self, state: ActiveState) -> None:
        self._workstream_id = state.workstream_id
        self._workstream_title = _markdown_title(state.workstream_spec) or state.workstream_id
        self._role = state.current_role or state.next_role or "Unassigned"
        self._declared_epoch = state.epoch_id
        self._task_id = state.task_id
        self._task_title = _markdown_title(state.task_spec) or state.task_id or "Active task"
        self._next_task_id = state.next_task_id
        self._next_task_title = _markdown_title(state.next_task_spec) or state.next_task_id
        self._human_gate = state.human_gate
        self._next_action = _continuation_label(state.continuation)
        self._next_reason = state.continuation_reason
        stages = _extract_stages(state.workstream_spec)
        self._stages = stages
        self._current_stage = _match_stage(
            stages,
            " ".join(
                part
                for part in (self._task_title, state.next_action, self._role)
                if part
            ),
        )

    def _refresh_repository_state_locked(self) -> None:
        try:
            state = parse_active(self.root)
        except (OSError, ValueError):
            return
        self._apply_active_state(state)

    def _next_role_from_repository(self) -> str:
        try:
            return parse_active(self.root).next_role or self._role
        except (OSError, ValueError):
            return self._role

    def _push_recent(
        self,
        kind: str,
        title: str,
        detail: str = "",
        level: str = "info",
    ) -> None:
        candidate = RecentEvent(kind, _single_line(title), _single_line(detail), level)
        if self._recent_events and self._recent_events[0] == candidate:
            return
        self._recent_events.appendleft(candidate)

    def _set_terminal_activity(self) -> None:
        if self._status == "COMPLETE":
            self._current_activity = Activity(
                "complete", "Workstream complete", self._task_title
            )
        elif self._status == "PAUSED":
            self._current_activity = Activity(
                "pause", "Operator action required", self._human_gate or self._reason
            )
        elif self._status in {"FAILED", "LIMIT_REACHED"}:
            self._current_activity = Activity(
                "error", "Supervisor stopped", self._reason
            )


def _usage(value: Any) -> TokenUsage:
    if not isinstance(value, dict):
        return TokenUsage()
    return TokenUsage(
        input_tokens=_integer(value.get("input_tokens")),
        cached_input_tokens=_integer(value.get("cached_input_tokens")),
        cache_write_input_tokens=_integer(value.get("cache_write_input_tokens")),
        output_tokens=_integer(value.get("output_tokens")),
        reasoning_output_tokens=_integer(value.get("reasoning_output_tokens")),
    )


def _activity_from_codex_event(event: dict[str, Any]) -> Activity | None:
    event_type = _string(event.get("type"))
    item = event.get("item")
    payload = item if isinstance(item, dict) else event
    item_type = _string(payload.get("type")).lower()

    if item_type in _REASONING_TYPES:
        return Activity("analyze", "Analyzing repository state")

    if item_type in _COMMAND_TYPES:
        command = _command_text(payload)
        state = "Running command" if event_type.endswith(".started") else "Command completed"
        return Activity("command", state, command)

    if item_type in _FILE_TYPES:
        paths = _file_paths(payload)
        if "read" in item_type:
            return Activity("read", "Inspecting repository files", paths)
        if event_type.endswith(".completed"):
            return Activity("edit", "Repository files updated", paths)
        return Activity("edit", "Editing repository files", paths)

    if item_type in _TOOL_TYPES:
        tool = _string(payload.get("name") or payload.get("tool") or payload.get("server"))
        state = "Calling tool" if event_type.endswith(".started") else "Tool call completed"
        return Activity("tool", state, tool)

    if item_type in {"web_search", "search"}:
        return Activity("search", "Searching supporting documentation")

    if item_type in {"todo_list", "plan", "task_list"}:
        return Activity("plan", "Updating the execution plan")

    if item_type in {"agent_message", "message"}:
        return Activity("report", "Preparing checkpoint report")

    # Some Codex releases place the actionable object directly on the event.
    command = _command_text(payload)
    if command:
        return Activity("command", "Running command", command)
    paths = _file_paths(payload)
    if paths:
        return Activity("edit", "Working with repository files", paths)
    return None


def _command_text(payload: dict[str, Any]) -> str:
    command = payload.get("command") or payload.get("cmd")
    if isinstance(command, list):
        return _truncate(" ".join(str(part) for part in command), 120)
    if isinstance(command, str):
        return _truncate(_single_line(command), 120)
    return ""


def _file_paths(payload: dict[str, Any]) -> str:
    paths: list[str] = []
    for key in ("path", "file_path", "filename"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            paths.append(value)
    changes = payload.get("changes")
    if isinstance(changes, list):
        for change in changes:
            if isinstance(change, dict):
                path = change.get("path") or change.get("file_path")
                if isinstance(path, str) and path:
                    paths.append(path)
    unique = list(dict.fromkeys(paths))
    return _truncate(", ".join(unique[:3]), 120)


def _markdown_title(path: Path | None) -> str:
    if path is None or not path.is_file():
        return ""
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                return re.sub(
                    r"^[A-Za-z0-9_.-]+(?:_[A-Za-z0-9_.-]+)*\s*[—–:]\s*",
                    "",
                    title,
                ).strip()
    except OSError:
        return ""
    return ""


def _extract_stages(path: Path | None) -> tuple[str, ...]:
    if path is None or not path.is_file():
        return ()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ()
    match = re.search(
        r"^##\s+(?:State Machine|Progress|Phases)\s*$\n(.*?)(?=^##\s+|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    if not match:
        return ()
    section = match.group(1).replace("```text", "").replace("```", "").strip()
    parts: list[str] = []
    for line in section.splitlines():
        stripped = line.strip().lstrip("- ")
        if not stripped:
            continue
        parts.extend(part.strip() for part in stripped.split("→") if part.strip())
    clean = tuple(_truncate(re.sub(r"\s+", " ", part), 28) for part in parts)
    return clean if 2 <= len(clean) <= 8 else ()


def _match_stage(stages: tuple[str, ...], context: str) -> int | None:
    if not stages:
        return None
    normalized_context = context.lower()
    context_tokens = _tokens(context)
    scores: list[int] = []
    for stage in stages:
        stage_tokens = _tokens(stage)
        score = len(stage_tokens & context_tokens)
        canonical = next(iter(stage_tokens), "") if len(stage_tokens) == 1 else ""
        aliases = {
            "design": ("design",),
            "implement": ("implementation", "implement"),
            "validate": ("validation", "validate", "testing", "test"),
            "run": ("formal execution", "benchmark run", "execution", "runner", "run"),
            "analyze": ("independent analysis", "analysis", "analyze", "analyst"),
            "review": ("independent review", "review", "reviewer"),
        }.get(canonical, ())
        for alias in aliases:
            if re.search(rf"\b{re.escape(alias)}\b", normalized_context):
                score += len(alias) + 2
        scores.append(score)
    best = max(scores, default=0)
    if best <= 0 or scores.count(best) > 1:
        return None
    return scores.index(best)


def _tokens(value: str) -> set[str]:
    aliases = {
        "analysis": "analyze",
        "analyst": "analyze",
        "implementation": "implement",
        "implemented": "implement",
        "validation": "validate",
        "validating": "validate",
        "verified": "validate",
        "verification": "validate",
        "execution": "run",
        "executing": "run",
        "runner": "run",
        "reviewer": "review",
        "reviewing": "review",
    }
    result: set[str] = set()
    for token in re.findall(r"[a-z0-9]+", value.lower()):
        if len(token) < 3 or token in {"task", "agent", "runtime", "current"}:
            continue
        result.add(aliases.get(token, token))
    return result


def _continuation_label(value: str) -> str:
    normalized = value.upper().strip()
    return {
        "CONTINUE_ALLOWED": "CONTINUE",
        "ROTATE_REQUIRED": "ROTATE",
        "STOP_REQUIRED": "PAUSE",
        "COMPLETE": "COMPLETE",
    }.get(normalized, normalized or "—")


def _display_name(value: str) -> str:
    words = re.split(r"[-_]+", value)
    return " ".join(word if word.isupper() else word.title() for word in words if word)


def _usage_detail(usage: TokenUsage) -> str:
    if not usage.input_tokens and not usage.output_tokens:
        return ""
    input_tokens = _compact_number(usage.input_tokens)
    output_tokens = _compact_number(usage.output_tokens)
    return f"{input_tokens} input · {output_tokens} output"


def _compact_number(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}m"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k"
    return str(value)


def _error_text(event: dict[str, Any]) -> str:
    value = event.get("error") or event.get("message")
    if isinstance(value, dict):
        return _string(value.get("message"))
    return _string(value)


def _integer(value: Any) -> int:
    return int(value) if isinstance(value, int | float) else 0


def _string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _join_strings(value: Any) -> str:
    if isinstance(value, list | tuple):
        return ", ".join(str(item) for item in value if item)
    return _string(value)


def _single_line(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _truncate(value: str, limit: int) -> str:
    value = _single_line(value)
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "…"
