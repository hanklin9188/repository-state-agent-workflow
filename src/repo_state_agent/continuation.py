from __future__ import annotations

from dataclasses import dataclass

from .model import ActiveState

CONTINUE_ALLOWED = "CONTINUE_ALLOWED"
ROTATE_REQUIRED = "ROTATE_REQUIRED"
STOP_REQUIRED = "STOP_REQUIRED"
VALID_CONTINUATIONS = {CONTINUE_ALLOWED, ROTATE_REQUIRED, STOP_REQUIRED}


@dataclass(frozen=True)
class ContinuationResult:
    action: str
    reasons: tuple[str, ...]

    @property
    def may_continue(self) -> bool:
        return self.action == "CONTINUE"


def _role(value: str) -> str:
    return value.strip().lower().replace("_", "-")


def decide_continuation(state: ActiveState) -> ContinuationResult:
    explicit = state.continuation.strip().upper() or ROTATE_REQUIRED

    if state.human_gate:
        return ContinuationResult("STOP_REQUIRED", ("HUMAN_GATE",))
    if explicit == STOP_REQUIRED:
        return ContinuationResult("STOP_REQUIRED", ("EXPLICIT_STOP",))
    if explicit == ROTATE_REQUIRED:
        reason = state.continuation_reason or "EXPLICIT_ROTATION"
        return ContinuationResult("ROTATE_REQUIRED", (reason,))
    if explicit not in VALID_CONTINUATIONS:
        return ContinuationResult("ROTATE_REQUIRED", ("INVALID_CONTINUATION_DECISION",))

    if state.next_task_spec is None or not state.next_task_spec.is_file():
        return ContinuationResult("ROTATE_REQUIRED", ("NEXT_TASK_NOT_READY",))

    current_role = _role(state.current_role)
    next_role = _role(state.next_role)
    if current_role and next_role and current_role != next_role:
        return ContinuationResult("ROTATE_REQUIRED", ("ROLE_CHANGE",))

    return ContinuationResult("CONTINUE", ("SAME_EPOCH",))
