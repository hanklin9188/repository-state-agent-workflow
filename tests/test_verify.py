from __future__ import annotations

from pathlib import Path

from repo_state_agent.verify import verify_repository


def _valid_repo(root: Path) -> None:
    (root / "docs/tasks").mkdir(parents=True)
    (root / "AGENTS.md").write_text("# Agent Policy\n", encoding="utf-8")
    (root / "docs/tasks/T-1.md").write_text("# Task\n", encoding="utf-8")
    (root / "ACTIVE.md").write_text(
        """# Active Handoff

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

## Next Session Role
Builder

## Recommended Reasoning
Medium
""",
        encoding="utf-8",
    )


def test_valid_repository(tmp_path: Path) -> None:
    _valid_repo(tmp_path)
    result = verify_repository(tmp_path)
    assert result.ok
    assert not result.errors


def test_missing_task_is_error(tmp_path: Path) -> None:
    _valid_repo(tmp_path)
    (tmp_path / "docs/tasks/T-1.md").unlink()
    result = verify_repository(tmp_path)
    assert not result.ok
    assert any("task spec" in error.lower() for error in result.errors)


def test_invalid_role_is_error(tmp_path: Path) -> None:
    _valid_repo(tmp_path)
    active = (tmp_path / "ACTIVE.md").read_text(encoding="utf-8")
    (tmp_path / "ACTIVE.md").write_text(active.replace("Builder", "Wizard"), encoding="utf-8")
    result = verify_repository(tmp_path)
    assert not result.ok
    assert any("role" in error.lower() for error in result.errors)
