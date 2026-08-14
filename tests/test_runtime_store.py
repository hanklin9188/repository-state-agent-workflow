from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from repo_state_agent.runtime.store import RuntimeLock


def test_runtime_lock_rejects_live_owner(tmp_path: Path) -> None:
    lock_path = tmp_path / ".rsaw/runtime.lock"
    lock_path.parent.mkdir(parents=True)
    lock_path.write_text(json.dumps({"pid": os.getpid()}), encoding="utf-8")
    with (
        pytest.raises(RuntimeError, match="Another RSAW supervisor"),
        RuntimeLock.for_root(tmp_path),
    ):
        pass


def test_runtime_lock_replaces_malformed_stale_lock(tmp_path: Path) -> None:
    lock_path = tmp_path / ".rsaw/runtime.lock"
    lock_path.parent.mkdir(parents=True)
    lock_path.write_text("malformed", encoding="utf-8")
    with RuntimeLock.for_root(tmp_path):
        assert lock_path.is_file()
    assert not lock_path.exists()
