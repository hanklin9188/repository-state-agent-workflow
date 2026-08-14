from __future__ import annotations

from pathlib import Path

from repo_state_agent.verify import verify_repository


def _valid_repo(root: Path, *, continue_allowed: bool = False, role_change: bool = False) -> None:
    (root / "docs/tasks").mkdir(parents=True)
    (root / "docs/workstreams").mkdir(parents=True)
    (root / "AGENTS.md").write_text("# Agent Policy\n", encoding="utf-8")
    (root / "docs/tasks/T-1.md").write_text("# Task\n", encoding="utf-8")
    (root / "docs/tasks/T-2.md").write_text("# Task 2\n", encoding="utf-8")
    (root / "docs/workstreams/W-1.md").write_text("# Workstream\n", encoding="utf-8")
    decision = "CONTINUE_ALLOWED" if continue_allowed else "ROTATE_REQUIRED"
    next_role = "Reviewer" if role_change else "Builder"
    next_task = (
        """## Next Task
ID: T-2
Spec: docs/tasks/T-2.md
"""
        if continue_allowed
        else "## Next Task\n\nNone.\n"
    )
    (root / "ACTIVE.md").write_text(
        f"""# Active Handoff

## Workstream
ID: W-1
Spec: docs/workstreams/W-1.md

## Context Epoch
ID: E-1
Role: Builder

## Active Task
ID: T-1
Spec: docs/tasks/T-1.md

## Required Reads
- AGENTS.md
- ACTIVE.md
- docs/tasks/T-1.md

## Next Exact Action
Do the task.

## Stop Condition
Tests pass.

## Continuation Gate
Decision: {decision}
Reason: test

{next_task}
## Human Gate
None.

## Next Session Role
{next_role}

## Recommended Reasoning
Medium
""",
        encoding="utf-8",
    )


def test_valid_repository(tmp_path: Path) -> None:
    _valid_repo(tmp_path)
    result = verify_repository(tmp_path)
    assert result.ok, result.errors


def test_continue_allowed_with_ready_same_role_task_is_valid(tmp_path: Path) -> None:
    _valid_repo(tmp_path, continue_allowed=True)
    result = verify_repository(tmp_path)
    assert result.ok, result.errors


def test_missing_task_is_error(tmp_path: Path) -> None:
    _valid_repo(tmp_path)
    (tmp_path / "docs/tasks/T-1.md").unlink()
    result = verify_repository(tmp_path)
    assert not result.ok
    assert any("task spec" in error.lower() for error in result.errors)


def test_invalid_role_is_error(tmp_path: Path) -> None:
    _valid_repo(tmp_path)
    active = (tmp_path / "ACTIVE.md").read_text(encoding="utf-8")
    (tmp_path / "ACTIVE.md").write_text(
        active.replace("Role: Builder", "Role: Wizard"), encoding="utf-8"
    )
    result = verify_repository(tmp_path)
    assert not result.ok
    assert any("role" in error.lower() for error in result.errors)


def test_continue_allowed_cannot_cross_role_boundary(tmp_path: Path) -> None:
    _valid_repo(tmp_path, continue_allowed=True, role_change=True)
    result = verify_repository(tmp_path)
    assert not result.ok
    assert any("role change" in error.lower() for error in result.errors)
