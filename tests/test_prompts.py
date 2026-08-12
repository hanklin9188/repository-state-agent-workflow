from __future__ import annotations

from pathlib import Path

from repo_state_agent.prompts import render_prompt


def test_builder_prompt_references_active_task(tmp_path: Path) -> None:
    (tmp_path / "docs/tasks").mkdir(parents=True)
    (tmp_path / "docs/tasks/T.md").write_text("task", encoding="utf-8")
    (tmp_path / "ACTIVE.md").write_text(
        """# Active
## Active Task
ID: T
Spec: docs/tasks/T.md
## Required Reads
- AGENTS.md
## Next Exact Action
Act.
## Stop Condition
Stop.
## Next Session Role
Builder
## Recommended Reasoning
Medium
""",
        encoding="utf-8",
    )
    prompt = render_prompt(tmp_path, "builder")
    assert "docs/tasks/T.md" in prompt
    assert "Execute exactly the active task" in prompt
