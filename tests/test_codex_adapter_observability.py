from __future__ import annotations

import sys
from pathlib import Path

from repo_state_agent.runtime.codex import CodexAdapter

SCRIPT = r'''import json
import sys

args = sys.argv[1:]
if args == ["--version"]:
    print("fake")
    raise SystemExit(0)
if args[:2] == ["exec", "--help"]:
    print("--json --output-last-message resume")
    raise SystemExit(0)
if args == ["login", "status"]:
    raise SystemExit(0)

print(json.dumps({"type": "thread.started", "thread_id": "thread-1"}), flush=True)
print(
    json.dumps(
        {
            "type": "item.started",
            "item": {"type": "command_execution", "command": "pytest -q"},
        }
    ),
    flush=True,
)
print(
    json.dumps(
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 10,
                "cached_input_tokens": 6,
                "output_tokens": 2,
                "reasoning_output_tokens": 1,
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
        f'#!/bin/sh\nexec {sys.executable} {path} "$@"\n', encoding="utf-8"
    )
    wrapper.chmod(0o755)
    return wrapper


def test_codex_adapter_forwards_structured_events(tmp_path: Path) -> None:
    events: list[dict[str, object]] = []
    adapter = CodexAdapter(
        binary=str(_script(tmp_path)),
        quiet=True,
        event_sink=events.append,
    )
    result = adapter.run_turn(
        prompt="work",
        root=tmp_path,
        run_dir=tmp_path / "run",
        turn_index=1,
        thread_id=None,
        environment={},
    )
    assert result.ok
    assert [event["type"] for event in events] == [
        "thread.started",
        "item.started",
        "turn.completed",
    ]


def test_observability_sink_failure_never_breaks_agent_turn(tmp_path: Path) -> None:
    def broken_sink(_: dict[str, object]) -> None:
        raise RuntimeError("presentation failed")

    adapter = CodexAdapter(
        binary=str(_script(tmp_path)),
        quiet=True,
        event_sink=broken_sink,
    )
    result = adapter.run_turn(
        prompt="work",
        root=tmp_path,
        run_dir=tmp_path / "run",
        turn_index=1,
        thread_id=None,
        environment={},
    )
    assert result.ok
