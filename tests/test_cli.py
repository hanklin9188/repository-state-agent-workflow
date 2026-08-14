from __future__ import annotations

from pathlib import Path

from repo_state_agent.cli import main
from repo_state_agent.scaffold import initialize_repository


def test_status_and_next_commands(tmp_path: Path, capsys) -> None:
    initialize_repository(tmp_path)
    assert main(["status", str(tmp_path)]) == 0
    status = capsys.readouterr().out
    assert "WORKSTREAM  W-000" in status
    assert "GATE        ROTATE_REQUIRED" in status

    assert main(["next", str(tmp_path)]) == 0
    decision = capsys.readouterr().out
    assert decision.startswith("ROTATE_REQUIRED")


def test_prompt_auto_command(tmp_path: Path, capsys) -> None:
    initialize_repository(tmp_path)
    assert main(["prompt", str(tmp_path)]) == 0
    prompt = capsys.readouterr().out
    assert "Resume the active RSAW workstream" in prompt
    assert "docs/tasks/T-000-bootstrap.md" in prompt
