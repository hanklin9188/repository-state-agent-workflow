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
    assert config.rotation_soft_input_tokens == 48_000
    assert config.bootstrap_token_budget == 15_000


def test_runtime_config_reads_legacy_limits(tmp_path: Path) -> None:
    (tmp_path / ".rsaw").mkdir()
    (tmp_path / ".rsaw/config.json").write_text(
        json.dumps({"runtime": {"max_turns_per_epoch": 3, "rotate_input_tokens": 40_000}}),
        encoding="utf-8",
    )
    config = load_runtime_config(tmp_path)
    assert config.max_turns_per_epoch == 3
    assert config.rotate_input_tokens == 40_000


def test_runtime_config_reads_nested_rotation_and_context(tmp_path: Path) -> None:
    (tmp_path / ".rsaw").mkdir()
    (tmp_path / ".rsaw/config.json").write_text(
        json.dumps(
            {
                "runtime": {
                    "rotation": {
                        "soft_input_tokens": 30_000,
                        "hard_input_tokens": 50_000,
                        "max_fresh_input_tokens": 12_000,
                        "min_cache_reuse_ratio": 0.7,
                    },
                    "context": {
                        "bootstrap_token_budget": 9_000,
                        "max_files": 8,
                        "enforce_budget": True,
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    config = load_runtime_config(tmp_path)
    assert config.rotation_soft_input_tokens == 30_000
    assert config.rotate_input_tokens == 50_000
    assert config.max_fresh_input_tokens == 12_000
    assert config.min_cache_reuse_ratio == 0.7
    assert config.bootstrap_token_budget == 9_000
    assert config.max_context_files == 8
    assert config.enforce_context_budget is True


def test_runtime_config_rejects_invalid_limit(tmp_path: Path) -> None:
    (tmp_path / ".rsaw").mkdir()
    (tmp_path / ".rsaw/config.json").write_text(
        json.dumps({"runtime": {"max_turns_per_epoch": 0}}), encoding="utf-8"
    )
    with pytest.raises(ValueError):
        load_runtime_config(tmp_path)


def test_runtime_config_rejects_soft_limit_above_hard_limit(tmp_path: Path) -> None:
    (tmp_path / ".rsaw").mkdir()
    (tmp_path / ".rsaw/config.json").write_text(
        json.dumps(
            {
                "runtime": {
                    "rotation": {
                        "soft_input_tokens": 70_000,
                        "hard_input_tokens": 60_000,
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_runtime_config(tmp_path)
