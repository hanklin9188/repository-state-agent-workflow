from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from repo_state_agent.runtime.codex import CodexAdapter


SCRIPT = r'''import json
import os
import subprocess
import sys
import time

mode = os.environ["FAKE_MODE"]
args = sys.argv[1:]
if args == ["--version"]:
    print("fake")
    raise SystemExit(0)
if args[:2] == ["exec", "--help"]:
    print("--json --output-last-message resume")
    raise SystemExit(0)
if args == ["login", "status"]:
    raise SystemExit(0)

if mode == "timeout":
    time.sleep(30)
elif mode == "missing-events":
    raise SystemExit(0)
elif mode == "inherited-stdout":
    subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    print(json.dumps({"type": "thread.started", "thread_id": "thread"}), flush=True)
    print(
        json.dumps(
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 1,
                    "cached_input_tokens": 0,
                    "output_tokens": 1,
                    "reasoning_output_tokens": 0,
                },
            }
        ),
        flush=True,
    )
'''


def _script(tmp_path: Path) -> Path:
    path = tmp_path / "fake_codex.py"
    path.write_text(SCRIPT, encoding="utf-8")
    wrapper = tmp_path / "codex-fake"
    wrapper.write_text(
        f"#!/bin/sh\nexec {sys.executable} {path} \"$@\"\n", encoding="utf-8"
    )
    wrapper.chmod(0o755)
    return wrapper


def test_turn_timeout_terminates_owned_process_group(tmp_path: Path) -> None:
    adapter = CodexAdapter(
        binary=str(_script(tmp_path)),
        quiet=True,
        turn_timeout_seconds=0.15,
        stdout_eof_grace_seconds=0.1,
    )
    result = adapter.run_turn(
        prompt="x",
        root=tmp_path,
        run_dir=tmp_path / "run",
        turn_index=1,
        thread_id=None,
        environment={"FAKE_MODE": "timeout"},
    )
    assert not result.ok
    assert result.exit_code == 124
    assert "exceeded" in result.error


def test_missing_json_terminal_events_fail_closed(tmp_path: Path) -> None:
    adapter = CodexAdapter(binary=str(_script(tmp_path)), quiet=True)
    result = adapter.run_turn(
        prompt="x",
        root=tmp_path,
        run_dir=tmp_path / "run",
        turn_index=1,
        thread_id=None,
        environment={"FAKE_MODE": "missing-events"},
    )
    assert not result.ok
    assert "thread.started" in result.error


@pytest.mark.skipif(os.name != "posix", reason="process-group inheritance test is POSIX-only")
def test_descendant_retaining_stdout_is_killed_and_fails_closed(tmp_path: Path) -> None:
    adapter = CodexAdapter(
        binary=str(_script(tmp_path)),
        quiet=True,
        turn_timeout_seconds=5,
        stdout_eof_grace_seconds=0.1,
    )
    result = adapter.run_turn(
        prompt="x",
        root=tmp_path,
        run_dir=tmp_path / "run",
        turn_index=1,
        thread_id=None,
        environment={"FAKE_MODE": "inherited-stdout"},
    )
    assert not result.ok
    assert result.exit_code == 124
    assert "stdout remained open" in result.error
