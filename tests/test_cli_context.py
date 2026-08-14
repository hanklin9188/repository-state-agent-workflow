from __future__ import annotations

import json
from pathlib import Path

from repo_state_agent.cli import main
from repo_state_agent.scaffold import initialize_repository


def test_context_command_reports_ordered_plan(tmp_path: Path, capsys) -> None:
    initialize_repository(tmp_path)
    assert main(["context", str(tmp_path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["documents"][0]["path"] == "AGENTS.md"
    assert payload["stable_tokens"] > 0
    assert payload["dynamic_tokens"] > 0
    assert payload["within_budget"] is True


def test_context_strict_fails_when_budget_is_exceeded(tmp_path: Path) -> None:
    initialize_repository(tmp_path)
    config = tmp_path / ".rsaw/config.json"
    raw = json.loads(config.read_text(encoding="utf-8"))
    raw["runtime"]["context"]["bootstrap_token_budget"] = 1
    config.write_text(json.dumps(raw), encoding="utf-8")
    assert main(["context", str(tmp_path), "--strict"]) == 1
