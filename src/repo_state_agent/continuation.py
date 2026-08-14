from __future__ import annotations

from dataclasses import dataclass

from .model import ActiveState

# Repository metadata values. The 0.2 names remain valid for compatibility.
CONTINUE_ALLOWED = "CONTINUE_ALLOWED"
ROTATE_REQUIRED = "ROTATE_REQUIRED"
STOP_REQUIRED = "STOP_REQUIRED"
COMPLETE = "COMPLETE"
VALID_CONTINUATIONS = {CONTINUE_ALLOWED, ROTATE_REQUIRED, STOP_REQUIRED, COMPLETE}

# Runtime actions. ROTATE keeps the workstream running; PAUSE is the only
# ordinary human/external stop.
ACTION_CONTINUE = "CONTINUE"
ACTION_ROTATE = "ROTATE"
ACTION_PAUSE = "PAUSE"
ACTION_COMPLETE = "COMPLETE"
VALID_ACTIONS = {ACTION_CONTINUE, ACTION_ROTATE, ACTION_PAUSE, ACTION_COMPLETE}


@dataclass(frozen=True)
class ContinuationResult:
    action: str
    reasons: tuple[str, ...]
    declared_decision: str

    @property
    def may_continue(self) -> bool:
        return self.action == ACTION_CONTINUE

    @property
    def should_rotate(self) -> bool:
        return self.action == ACTION_ROTATE

    @property
    def paused(self) -> bool:
        return self.action == ACTION_PAUSE

    @property
    def complete(self) -> bool:
        return self.action == ACTION_COMPLETE


def _role(value: str) -> str:
    return value.strip().lower().replace("_", "-")


def decide_continuation(state: ActiveState) -> ContinuationResult:
    declared = state.continuation.strip().upper() or ROTATE_REQUIRED

    if state.human_gate:
        return ContinuationResult(ACTION_PAUSE, ("HUMAN_GATE",), declared)
    if declared == COMPLETE:
        return ContinuationResult(ACTION_COMPLETE, ("WORKSTREAM_COMPLETE",), declared)
    if declared == STOP_REQUIRED:
        reason = state.continuation_reason or "EXPLICIT_PAUSE"
        return ContinuationResult(ACTION_PAUSE, (reason,), declared)
    if declared == ROTATE_REQUIRED:
        reason = state.continuation_reason or "EXPLICIT_ROTATION"
        return ContinuationResult(ACTION_ROTATE, (reason,), declared)
    if declared not in VALID_CONTINUATIONS:
        return ContinuationResult(
            ACTION_ROTATE, ("INVALID_CONTINUATION_DECISION",), declared
        )

    if state.next_task_spec is None or not state.next_task_spec.is_file():
        return ContinuationResult(ACTION_ROTATE, ("NEXT_TASK_NOT_READY",), declared)

    current_role = _role(state.current_role)
    next_role = _role(state.next_role)
    if current_role and next_role and current_role != next_role:
        return ContinuationResult(ACTION_ROTATE, ("ROLE_CHANGE",), declared)

    return ContinuationResult(ACTION_CONTINUE, ("SAME_EPOCH",), declared)
