from __future__ import annotations

from pathlib import Path

from repo_state_agent.continuation import decide_continuation
from repo_state_agent.parsing import parse_active


def _write_state(
    root: Path, decision: str, next_role: str = "Builder", gate: str = "None."
) -> None:
    (root / "docs/tasks").mkdir(parents=True)
    (root / "docs/workstreams").mkdir(parents=True)
    (root / "docs/tasks/T.md").write_text("task", encoding="utf-8")
    (root / "docs/tasks/T2.md").write_text("task2", encoding="utf-8")
    (root / "docs/workstreams/W.md").write_text("workstream", encoding="utf-8")
    (root / "ACTIVE.md").write_text(
        f"""# Active
## Workstream
ID: W
Spec: docs/workstreams/W.md
## Context Epoch
ID: E
Role: Builder
## Active Task
ID: T
Spec: docs/tasks/T.md
## Required Reads
- ACTIVE.md
## Next Exact Action
Act.
## Stop Condition
Checkpoint.
## Continuation Gate
Decision: {decision}
Reason: same epoch
## Next Task
ID: T2
Spec: docs/tasks/T2.md
## Human Gate
{gate}
## Next Session Role
{next_role}
## Recommended Reasoning
Medium
""",
        encoding="utf-8",
    )


def test_same_role_ready_task_can_continue(tmp_path: Path) -> None:
    _write_state(tmp_path, "CONTINUE_ALLOWED")
    result = decide_continuation(parse_active(tmp_path))
    assert result.action == "CONTINUE"


def test_role_change_forces_rotation(tmp_path: Path) -> None:
    _write_state(tmp_path, "CONTINUE_ALLOWED", next_role="Reviewer")
    result = decide_continuation(parse_active(tmp_path))
    assert result.action == "ROTATE_REQUIRED"
    assert "ROLE_CHANGE" in result.reasons


def test_human_gate_forces_stop(tmp_path: Path) -> None:
    _write_state(tmp_path, "CONTINUE_ALLOWED", gate="Approve production deployment.")
    result = decide_continuation(parse_active(tmp_path))
    assert result.action == "STOP_REQUIRED"
    assert "HUMAN_GATE" in result.reasons
