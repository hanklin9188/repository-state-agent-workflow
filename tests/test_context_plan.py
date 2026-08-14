from __future__ import annotations

from pathlib import Path

from repo_state_agent.runtime.context import build_context_plan


def _repo(root: Path) -> None:
    (root / "docs/tasks").mkdir(parents=True)
    (root / "docs/workstreams").mkdir(parents=True)
    (root / "AGENTS.md").write_text("# Policy\nstable\n", encoding="utf-8")
    (root / "docs/tasks/T-1.md").write_text("# Task\ndynamic\n", encoding="utf-8")
    (root / "docs/tasks/T-2.md").write_text("# Next\n", encoding="utf-8")
    (root / "docs/workstreams/W-1.md").write_text("# Workstream\n", encoding="utf-8")
    (root / "ACTIVE.md").write_text(
        """# Active Handoff

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

## Human Gate
None.

## Next Exact Action
Do it.

## Stop Condition
Done.

## Continuation Gate
Decision: CONTINUE_ALLOWED
Reason: SAME_TASK

## Next Task
ID: T-2
Spec: docs/tasks/T-2.md

## Next Session Role
Builder

## Recommended Reasoning
Medium
""",
        encoding="utf-8",
    )


def test_context_plan_is_ordered_deduplicated_and_fingerprinted(tmp_path: Path) -> None:
    _repo(tmp_path)
    plan = build_context_plan(tmp_path, budget_tokens=10_000)
    assert [document.path for document in plan.documents] == [
        "AGENTS.md",
        "ACTIVE.md",
        "docs/tasks/T-1.md",
    ]
    assert plan.documents[0].category == "stable"
    assert plan.stable_tokens > 0
    assert plan.dynamic_tokens > 0
    assert plan.within_budget
    assert len(plan.stable_fingerprint) == 64


def test_stable_fingerprint_ignores_dynamic_changes(tmp_path: Path) -> None:
    _repo(tmp_path)
    first = build_context_plan(tmp_path)
    task = tmp_path / "docs/tasks/T-1.md"
    task.write_text("# Task\nchanged dynamic content\n", encoding="utf-8")
    second = build_context_plan(tmp_path)
    assert first.stable_fingerprint == second.stable_fingerprint
    assert first.dynamic_fingerprint != second.dynamic_fingerprint


def test_context_plan_reports_budget_and_file_limits(tmp_path: Path) -> None:
    _repo(tmp_path)
    plan = build_context_plan(tmp_path, budget_tokens=1, max_files=2)
    assert not plan.ok
    assert not plan.within_budget
    assert any("configured maximum" in error for error in plan.errors)
