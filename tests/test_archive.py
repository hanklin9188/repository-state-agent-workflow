from __future__ import annotations

from datetime import date
from pathlib import Path

from repo_state_agent.archive import archive_active


def test_archive_active(tmp_path: Path) -> None:
    (tmp_path / "ACTIVE.md").write_text("state", encoding="utf-8")
    target = archive_active(tmp_path, "T-42 complete", archive_date=date(2026, 8, 12))
    assert target.name == "2026-08-12_T-42-complete.md"
    assert target.read_text(encoding="utf-8") == "state"
