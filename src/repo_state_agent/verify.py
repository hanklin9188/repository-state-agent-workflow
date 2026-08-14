from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .continuation import CONTINUE_ALLOWED, VALID_CONTINUATIONS
from .parsing import parse_active

VALID_ROLES = {"builder", "reviewer", "decision", "runner", "analyst"}
VALID_REASONING = {"low", "medium", "high", "extra high", "xhigh", "ultra"}


@dataclass
class VerificationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _role(value: str) -> str:
    return value.strip().lower().replace("_", "-")


def verify_repository(
    root: Path, max_lines: int = 140, max_bytes: int = 12_288
) -> VerificationResult:
    root = root.resolve()
    result = VerificationResult()
    active_path = root / "ACTIVE.md"
    agents_path = root / "AGENTS.md"

    if not agents_path.is_file():
        result.errors.append("AGENTS.md is missing")
    if not active_path.is_file():
        result.errors.append("ACTIVE.md is missing")
        return result

    raw = active_path.read_bytes()
    text = raw.decode("utf-8")
    line_count = len(text.splitlines())
    if line_count > max_lines:
        result.errors.append(f"ACTIVE.md has {line_count} lines; limit is {max_lines}")
    if len(raw) > max_bytes:
        result.errors.append(f"ACTIVE.md has {len(raw)} bytes; limit is {max_bytes}")

    try:
        state = parse_active(root)
    except Exception as exc:  # pragma: no cover - defensive boundary
        result.errors.append(f"ACTIVE.md could not be parsed: {exc}")
        return result

    if not state.task_id:
        result.errors.append("Active Task ID is missing")
    if not state.task_spec.is_file():
        result.errors.append(f"Active task spec does not exist: {state.task_spec}")

    if state.workstream_id or state.workstream_spec is not None:
        if not state.workstream_id:
            result.errors.append("Workstream ID is missing")
        if state.workstream_spec is None or not state.workstream_spec.is_file():
            result.errors.append(f"Workstream spec does not exist: {state.workstream_spec}")
        if not state.epoch_id:
            result.errors.append("Context Epoch ID is missing")
        if not state.current_role:
            result.errors.append("Context Epoch Role is missing")

    if not state.required_reads:
        result.warnings.append("Required Reads is empty")
    for path in state.required_reads:
        if not path.exists():
            result.errors.append(f"Required read does not exist: {path}")

    if not state.next_action:
        result.errors.append("Next Exact Action is empty")
    if not state.stop_condition:
        result.errors.append("Stop Condition is empty")

    next_role = _role(state.next_role)
    if next_role not in VALID_ROLES:
        result.errors.append(
            f"Next Session Role must be one of {sorted(VALID_ROLES)}; got {state.next_role!r}"
        )

    if state.current_role and _role(state.current_role) not in VALID_ROLES:
        result.errors.append(
            f"Context Epoch Role must be one of {sorted(VALID_ROLES)}; "
            f"got {state.current_role!r}"
        )

    if state.reasoning.lower() not in VALID_REASONING:
        result.errors.append(
            f"Recommended Reasoning must be one of {sorted(VALID_REASONING)}; "
            f"got {state.reasoning!r}"
        )

    continuation = state.continuation.strip().upper()
    if continuation not in VALID_CONTINUATIONS:
        result.errors.append(
            f"Continuation decision must be one of {sorted(VALID_CONTINUATIONS)}; "
            f"got {state.continuation!r}"
        )

    if state.next_task_id or state.next_task_spec is not None:
        if not state.next_task_id:
            result.errors.append("Next Task ID is missing")
        if state.next_task_spec is None or not state.next_task_spec.is_file():
            result.errors.append(f"Next task spec does not exist: {state.next_task_spec}")

    if continuation == CONTINUE_ALLOWED:
        if state.next_task_spec is None or not state.next_task_spec.is_file():
            result.errors.append("CONTINUE_ALLOWED requires a ready next task spec")
        if state.human_gate:
            result.errors.append("CONTINUE_ALLOWED is incompatible with an active Human Gate")
        if state.current_role and _role(state.current_role) != next_role:
            result.errors.append("CONTINUE_ALLOWED is incompatible with a role change")

    fenced_blocks = re.findall(r"```.*?```", text, flags=re.DOTALL)
    large_blocks = [block for block in fenced_blocks if len(block.splitlines()) > 20]
    if large_blocks:
        result.warnings.append("ACTIVE.md contains a code block longer than 20 lines")

    suspicious = ("Traceback (most recent call last)", "BEGIN RAW LOG", "tool_output")
    for marker in suspicious:
        if marker in text:
            result.warnings.append(f"ACTIVE.md may contain raw log content: {marker}")

    return result
