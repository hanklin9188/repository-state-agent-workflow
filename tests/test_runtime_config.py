from __future__ import annotations

import json
from pathlib import Path

import pytest

from repo_state_agent.runtime.config import load_runtime_config


def test_runtime_config_defaults_without_file(tmp_path: Path) -> None:
    config = load_runtime_config(tmp_path)
    assert config.adapter == "codex"
    assert config.sandbox == "workspace-write"
    assert config.approve_for_me is False


def test_runtime_config_reads_limits(tmp_path: Path) -> None:
    (tmp_path / ".rsaw").mkdir()
    (tmp_path / ".rsaw/config.json").write_text(
        json.dumps({"runtime": {"max_turns_per_epoch": 3, "rotate_input_tokens": 40000}}),
        encoding="utf-8",
    )
    config = load_runtime_config(tmp_path)
    assert config.max_turns_per_epoch == 3
    assert config.rotate_input_tokens == 40000


def test_runtime_config_rejects_invalid_limit(tmp_path: Path) -> None:
    (tmp_path / ".rsaw").mkdir()
    (tmp_path / ".rsaw/config.json").write_text(
        json.dumps({"runtime": {"max_turns_per_epoch": 0}}), encoding="utf-8"
    )
    with pytest.raises(ValueError):
        load_runtime_config(tmp_path)
