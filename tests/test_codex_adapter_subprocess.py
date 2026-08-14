from repo_state_agent.runtime.codex import CodexAdapter


FAKE_CODEX = r'''#!/usr/bin/env python3
import json
import pathlib
import sys

args = sys.argv[1:]
if args == ["--version"]:
    print("codex-cli fake-1.0")
    raise SystemExit(0)
if args[:2] == ["exec", "--help"]:
    print("--json --output-last-message resume")
    raise SystemExit(0)

prompt = sys.stdin.read()
output_path = pathlib.Path(args[args.index("--output-last-message") + 1])
thread_id = "thread-fresh"
if "resume" in args:
    thread_id = args[args.index("resume") + 1]
print(json.dumps({"type": "thread.started", "thread_id": thread_id}), flush=True)
print(
    json.dumps(
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": len(prompt),
                "cached_input_tokens": 7,
                "cache_write_input_tokens": 3,
                "output_tokens": 5,
                "reasoning_output_tokens": 2,
            },
        }
    ),
    flush=True,
)
output_path.write_text("checkpoint complete", encoding="utf-8")
'''


def _fake_binary(tmp_path):
    binary = tmp_path / "codex-fake"
    binary.write_text(FAKE_CODEX, encoding="utf-8")
    binary.chmod(0o755)
    return binary


def test_codex_adapter_doctor_and_fresh_resume_round_trip(tmp_path):
    binary = _fake_binary(tmp_path)
    adapter = CodexAdapter(binary=str(binary), quiet=True)

    doctor = adapter.doctor()
    assert doctor.ok
    assert set(doctor.capabilities) == {"exec-json", "exec-resume", "last-message"}

    run_dir = tmp_path / "runtime"
    fresh = adapter.run_turn(
        prompt="first checkpoint",
        root=tmp_path,
        run_dir=run_dir,
        turn_index=1,
        thread_id=None,
        environment={},
    )
    assert fresh.ok
    assert fresh.thread_id == "thread-fresh"
    assert fresh.usage.cached_input_tokens == 7
    assert fresh.last_message == "checkpoint complete"
    assert fresh.events_path and fresh.events_path.is_file()

    resumed = adapter.run_turn(
        prompt="second checkpoint",
        root=tmp_path,
        run_dir=run_dir,
        turn_index=2,
        thread_id=fresh.thread_id,
        environment={},
    )
    assert resumed.ok
    assert resumed.thread_id == "thread-fresh"
    assert resumed.usage.output_tokens == 5
