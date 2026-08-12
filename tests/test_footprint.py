from __future__ import annotations

from pathlib import Path

from repo_state_agent.footprint import measure_bootstrap


def test_measure_bootstrap_deduplicates_required_reads(tmp_path: Path) -> None:
    (tmp_path / "docs/tasks").mkdir(parents=True)
    (tmp_path / "AGENTS.md").write_text("policy", encoding="utf-8")
    (tmp_path / "docs/tasks/T.md").write_text("task", encoding="utf-8")
    (tmp_path / "ACTIVE.md").write_text(
        """# Active
## Active Task
ID: T
Spec: docs/tasks/T.md
## Required Reads
- AGENTS.md
- ACTIVE.md
- docs/tasks/T.md
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
    rows = measure_bootstrap(tmp_path)
    assert len(rows) == 3
    assert sum(row.approx_tokens for row in rows) > 0
