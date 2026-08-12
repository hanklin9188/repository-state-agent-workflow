from __future__ import annotations

from pathlib import Path

from repo_state_agent.scaffold import initialize_repository
from repo_state_agent.verify import verify_repository


def test_initialize_creates_core_files(tmp_path: Path) -> None:
    created, skipped = initialize_repository(tmp_path)
    assert not skipped
    assert tmp_path.joinpath("AGENTS.md").is_file()
    assert tmp_path.joinpath("ACTIVE.md").is_file()
    assert tmp_path.joinpath("docs/tasks/T-000-bootstrap.md").is_file()
    assert created


def test_initialize_does_not_overwrite_by_default(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("custom", encoding="utf-8")
    _, skipped = initialize_repository(tmp_path)
    assert tmp_path.joinpath("AGENTS.md") in skipped
    assert tmp_path.joinpath("AGENTS.md").read_text(encoding="utf-8") == "custom"


def test_initialized_repository_verifies(tmp_path: Path) -> None:
    initialize_repository(tmp_path)
    result = verify_repository(tmp_path)
    assert result.ok, result.errors
