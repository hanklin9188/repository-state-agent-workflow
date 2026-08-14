from __future__ import annotations

from pathlib import Path

from repo_state_agent.prompts import render_prompt


def _workstream_repo(root: Path) -> None:
    (root / "docs/tasks").mkdir(parents=True)
    (root / "docs/workstreams").mkdir(parents=True)
    (root / "AGENTS.md").write_text("policy", encoding="utf-8")
    (root / "docs/tasks/T.md").write_text("task", encoding="utf-8")
    (root / "docs/tasks/T2.md").write_text("task2", encoding="utf-8")
    (root / "docs/workstreams/W.md").write_text("workstream", encoding="utf-8")
    (root / "ACTIVE.md").write_text(
        """# Active
## Workstream
ID: W
Spec: docs/workstreams/W.md
## Context Epoch
ID: E-1
Role: Builder
## Active Task
ID: T
Spec: docs/tasks/T.md
## Required Reads
- AGENTS.md
## Next Exact Action
Act.
## Stop Condition
Checkpoint.
## Continuation Gate
Decision: CONTINUE_ALLOWED
Reason: same subsystem
## Next Task
ID: T2
Spec: docs/tasks/T2.md
## Human Gate
None.
## Next Session Role
Builder
## Recommended Reasoning
Medium
""",
        encoding="utf-8",
    )


def test_auto_prompt_references_active_task_and_gate(tmp_path: Path) -> None:
    _workstream_repo(tmp_path)
    prompt = render_prompt(tmp_path)
    assert "docs/tasks/T.md" in prompt
    assert "Continue the active RSAW context epoch" in prompt
    assert "run `rsaw next .`" in prompt


def test_fresh_reviewer_prompt_is_role_specific(tmp_path: Path) -> None:
    _workstream_repo(tmp_path)
    prompt = render_prompt(tmp_path, role="reviewer", mode="fresh")
    assert "Resume the active RSAW workstream" in prompt
    assert "Act as a fresh reviewer" in prompt
