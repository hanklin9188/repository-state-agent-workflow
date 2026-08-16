from __future__ import annotations

import json
import subprocess
from pathlib import Path

import repo_state_agent.v7_cli as cli_module
from repo_state_agent.v7_cli import main


def _repo(root: Path) -> None:
    subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    (root / "docs/tasks").mkdir(parents=True)
    (root / "docs/workstreams").mkdir(parents=True)
    (root / "src").mkdir()
    (root / ".rsaw").mkdir()
    (root / "AGENTS.md").write_text("# Policy\n")
    (root / "docs/workstreams/W.md").write_text("# W\n")
    (root / "docs/tasks/T.md").write_text(
        """# Parser repair

Update `src/parser.py` function `parse_packet`.

## Allowed Writes
- src/parser.py

## Validation
- `python -m pytest -q`
"""
    )
    (root / "src/parser.py").write_text("def parse_packet(value):\n    return value.strip()\n")
    (root / "ACTIVE.md").write_text(
        """# Active Handoff

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
- ACTIVE.md
- docs/tasks/T.md

## Human Gate
None.

## Next Exact Action
Repair parse_packet.

## Stop Condition
Validation passes.

## Continuation Gate
Decision: CONTINUE_ALLOWED
Reason: same role

## Next Task
ID: T
Spec: docs/tasks/T.md

## Next Session Role
Builder

## Recommended Reasoning
Medium
"""
    )
    (root / ".rsaw/config.json").write_text(
        json.dumps(
            {
                "schema_version": 4,
                "runtime": {
                    "v6": {"enabled": True},
                },
            }
        )
        + "\n"
    )
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd=root,
        check=True,
    )


def test_focus_command_reports_selected_working_set(tmp_path: Path, capsys) -> None:
    _repo(tmp_path)
    assert main(["focus", str(tmp_path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["enabled"] is True
    assert "src/parser.py" in payload["selectedFiles"]
    assert payload["totalTokens"] > 0


def test_upgrade_targets_v08_and_preserves_active(tmp_path: Path, capsys) -> None:
    _repo(tmp_path)
    before = (tmp_path / "ACTIVE.md").read_bytes()

    assert main(["upgrade", str(tmp_path), "--apply", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["target"] == "0.8"
    assert payload["status"] == "MIGRATED"
    assert (tmp_path / "ACTIVE.md").read_bytes() == before
    config = json.loads((tmp_path / ".rsaw/config.json").read_text())
    assert config["schema_version"] == 5
    assert config["runtime"]["relevance"]["enabled"] is True


def test_installation_view_uses_virtualenv_prefix_not_resolved_python(
    tmp_path: Path, monkeypatch
) -> None:
    prefix = tmp_path / "venv"
    launcher = prefix / "bin/rsaw"
    launcher.parent.mkdir(parents=True)
    launcher.write_text("#!/bin/sh\n")

    monkeypatch.setattr(cli_module.sys, "prefix", str(prefix))
    monkeypatch.setattr(cli_module.sys, "base_prefix", "/usr")
    monkeypatch.setattr(cli_module.shutil, "which", lambda _name: str(launcher))

    view = cli_module._installation_view()

    assert view["launcherMatchesPythonPrefix"] is True
    assert view["pythonPrefix"] == str(prefix)


def test_help_and_version_surface_v08(capsys) -> None:
    assert main(["--version"]) == 0
    assert "0.8.0" in capsys.readouterr().out
    assert main(["--help"]) == 0
    help_text = capsys.readouterr().out
    assert "rsaw focus ." in help_text
    assert "--to 0.8" in help_text
