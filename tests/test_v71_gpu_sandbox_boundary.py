from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

import repo_state_agent.v7_cli as cli_module
from repo_state_agent.runtime.codex import CodexAdapter
from repo_state_agent.runtime.model import AdapterDoctorResult, AgentTurnResult, TokenUsage
from repo_state_agent.runtime.tui.v6 import LiveDashboardV6
from repo_state_agent.runtime.v6 import (
    V6Options,
    V6SupervisorResult,
    supervise_v6,
    synthetic_acceptance,
)
from repo_state_agent.v7_cli import main as cli_main


def _repo(root: Path) -> None:
    subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    (root / ".rsaw/state/checkpoints").mkdir(parents=True)
    (root / "docs/tasks").mkdir(parents=True)
    (root / "docs/workstreams").mkdir(parents=True)
    (root / "AGENTS.md").write_text("# Policy\n", encoding="utf-8")
    (root / "docs/workstreams/W.md").write_text("# W\n", encoding="utf-8")
    task = """# Task

## Allowed Writes
- src/**
- tests/**

## Validation
- `python -m pytest -q`
"""
    (root / "docs/tasks/GPU.md").write_text(task, encoding="utf-8")
    (root / "docs/tasks/ANALYST.md").write_text(task, encoding="utf-8")
    (root / "ACTIVE.md").write_text(
        """# Active Handoff

## Workstream
ID: W
Spec: docs/workstreams/W.md

## Context Epoch
ID: E-1
Role: Runner

## Active Task
ID: GPU
Spec: docs/tasks/GPU.md

## Required Reads
- AGENTS.md
- ACTIVE.md
- docs/tasks/GPU.md

## Human Gate
None.

## Next Exact Action
Run the reviewed infrastructure boundary.

## Stop Condition
Boundary closes.

## Continuation Gate
Decision: CONTINUE_ALLOWED
Reason: same role

## Next Task
ID: ANALYST
Spec: docs/tasks/ANALYST.md

## Next Session Role
Runner

## Recommended Reasoning
Medium
""",
        encoding="utf-8",
    )
    (root / ".rsaw/config.json").write_text(
        json.dumps(
            {
                "schema_version": 4,
                "runtime": {
                    "max_transitions": 4,
                    "v6": {"enabled": True},
                    "codex": {
                        "binary": "codex",
                        "defaultSandbox": "workspace-write",
                        "taskSandboxOverrides": {"GPU": "danger-full-access"},
                    },
                },
            }
        ),
        encoding="utf-8",
    )


def _payload(task: str) -> dict[str, object]:
    complete = task == "ANALYST"
    return {
        "schemaVersion": "rsaw.checkpoint-result.v1",
        "outcome": "PASS",
        "summary": f"{task} complete",
        "changedFiles": [],
        "validations": [{"command": "python -m pytest -q", "status": "PASS"}],
        "artifacts": [],
        "semanticCapsuleDelta": {
            "observedFacts": [],
            "decisions": [],
            "excludedHypotheses": [],
            "evidenceRefs": [],
            "unresolvedRisks": [],
            "codeRelations": [],
            "validationStatus": [],
            "nextAction": "continue",
        },
        "nextTask": (
            None
            if complete
            else {
                "taskId": "ANALYST",
                "taskSpec": "docs/tasks/ANALYST.md",
                "role": "Runner",
            }
        ),
        "followingTask": None,
        "nextAction": "Close." if complete else "Continue safely.",
        "stopCondition": "Complete." if complete else "Next task completes.",
        "requestedAction": "COMPLETE" if complete else "CONTINUE",
        "transitionReason": "done" if complete else "same role, new sandbox",
        "humanGate": "",
    }


class _TaskAwareAdapter:
    name = "fake"

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def doctor(self) -> AdapterDoctorResult:
        return AdapterDoctorResult(ok=True, adapter="fake", binary="fake")

    def resolve_turn_settings(self, environment: dict[str, str]) -> dict[str, str]:
        task = environment["RSAW_TASK_ID"]
        sandbox = "danger-full-access" if task == "GPU" else "workspace-write"
        source = "task override" if task == "GPU" else "default"
        return {"task": task, "sandbox": sandbox, "source": source}

    def run_turn(
        self,
        *,
        prompt: str,
        root: Path,
        run_dir: Path,
        turn_index: int,
        thread_id: str | None,
        environment: dict[str, str],
    ) -> AgentTurnResult:
        task = environment["RSAW_TASK_ID"]
        self.calls.append(
            {
                "task": task,
                "sandbox": environment["RSAW_RESOLVED_SANDBOX"],
                "thread": thread_id,
            }
        )
        events = run_dir / f"turn-{turn_index:04d}.jsonl"
        events.write_text(
            "\n".join(
                json.dumps(row)
                for row in (
                    {
                        "type": "item.started",
                        "item": {
                            "id": f"cmd-{turn_index}",
                            "type": "command_execution",
                            "command": "python -m pytest -q",
                        },
                    },
                    {
                        "type": "item.completed",
                        "item": {
                            "id": f"cmd-{turn_index}",
                            "type": "command_execution",
                            "command": "python -m pytest -q",
                            "aggregated_output": "1 passed",
                            "exit_code": 0,
                        },
                    },
                )
            )
            + "\n",
            encoding="utf-8",
        )
        message = json.dumps(_payload(task))
        last = run_dir / f"turn-{turn_index:04d}-last-message.txt"
        last.write_text(message, encoding="utf-8")
        return AgentTurnResult(
            exit_code=0,
            thread_id=f"thread-{turn_index}",
            usage=TokenUsage(input_tokens=10),
            latest_turn_usage=TokenUsage(input_tokens=10),
            last_message=message,
            events_path=events,
            last_message_path=last,
        )


def test_task_sandbox_is_resolved_each_turn_and_forces_boundary_rotation(tmp_path: Path) -> None:
    _repo(tmp_path)
    adapter = _TaskAwareAdapter()
    result = supervise_v6(tmp_path, adapter, V6Options(max_transitions=3))
    assert result.status == "COMPLETE"
    assert adapter.calls == [
        {"task": "GPU", "sandbox": "danger-full-access", "thread": None},
        {"task": "ANALYST", "sandbox": "workspace-write", "thread": None},
    ]
    summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
    assert [row["sandbox"] for row in summary["sandbox_resolutions"]] == [
        "danger-full-access",
        "workspace-write",
    ]
    events = (result.summary_path.parent / "supervisor-events.jsonl").read_text(encoding="utf-8")
    assert '"type": "v7.sandbox.boundary"' in events
    assert '"toSandbox": "workspace-write"' in events


def test_sandbox_set_and_clear_require_reason_and_write_content_bound_audits(
    tmp_path: Path, capsys
) -> None:
    _repo(tmp_path)
    with pytest.raises(SystemExit):
        cli_main(
            [
                "sandbox",
                "set",
                str(tmp_path),
                "--task",
                "current",
                "--mode",
                "danger-full-access",
                "--yes",
            ]
        )
    capsys.readouterr()
    assert (
        cli_main(
            [
                "sandbox",
                "set",
                str(tmp_path),
                "--task",
                "current",
                "--mode",
                "danger-full-access",
                "--reason",
                "reviewed GPU boundary",
                "--yes",
                "--json",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    audit = json.loads((tmp_path / payload["audit"]).read_text(encoding="utf-8"))
    digest = audit.pop("contentSha256")
    canonical = json.dumps(audit, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert digest == hashlib.sha256(canonical).hexdigest()
    assert audit["reason"] == "reviewed GPU boundary"
    assert audit["operator"]["user"]
    assert audit["operator"]["hostname"]
    assert isinstance(audit["operator"]["pid"], int)
    assert (
        audit["afterConfigSha256"]
        == hashlib.sha256((tmp_path / ".rsaw/config.json").read_bytes()).hexdigest()
    )
    assert (
        cli_main(
            [
                "sandbox",
                "clear",
                str(tmp_path),
                "--task",
                "current",
                "--reason",
                "Runner boundary closed",
                "--yes",
                "--json",
            ]
        )
        == 0
    )
    clear_payload = json.loads(capsys.readouterr().out)
    assert (tmp_path / clear_payload["audit"]).is_file()
    config = json.loads((tmp_path / ".rsaw/config.json").read_text(encoding="utf-8"))
    assert "GPU" not in config["runtime"]["codex"]["taskSandboxOverrides"]


def test_sandbox_audit_failure_rolls_back_config(tmp_path: Path, monkeypatch, capsys) -> None:
    _repo(tmp_path)
    before = (tmp_path / ".rsaw/config.json").read_bytes()

    def fail_audit(*_args, **_kwargs):
        raise OSError("synthetic audit failure")

    monkeypatch.setattr(cli_module, "_write_operator_action", fail_audit)
    rc = cli_main(
        [
            "sandbox",
            "set",
            str(tmp_path),
            "--task",
            "current",
            "--mode",
            "danger-full-access",
            "--reason",
            "reviewed GPU boundary",
            "--yes",
            "--json",
        ]
    )
    assert rc == 1
    assert (tmp_path / ".rsaw/config.json").read_bytes() == before
    assert "synthetic audit failure" in capsys.readouterr().err


def test_expected_non_tui_pause_exits_zero_unless_strict(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _repo(tmp_path)

    def paused(*_args, **_kwargs) -> V6SupervisorResult:
        return V6SupervisorResult("PAUSED", "HUMAN_GATE", "run", None, 20)

    monkeypatch.setattr(cli_module, "supervise_v6", paused)
    assert cli_main(["run", str(tmp_path), "--no-tui", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "PAUSED"
    assert payload["exit_code"] == 20
    assert payload["runtime"] == "v0.8.0"
    assert (
        cli_main(
            [
                "run",
                str(tmp_path),
                "--no-tui",
                "--json",
                "--strict-exit-codes",
            ]
        )
        == 20
    )
    capsys.readouterr()


def test_acceptance_uses_next_phase_and_version_is_explicit(tmp_path: Path, capsys) -> None:
    _repo(tmp_path)
    results = [synthetic_acceptance(tmp_path, horizon) for horizon in (4, 16, 64)]
    assert all(result["pass"] for result in results)
    assert results[0]["rotations"] >= 1
    assert cli_main(["--version"]) == 0
    assert capsys.readouterr().out.strip() == "RSAW 0.8.0"


def test_explicit_cli_sandbox_is_scoped_to_one_task() -> None:
    adapter = CodexAdapter(
        sandbox="workspace-write",
        forced_sandbox="danger-full-access",
        forced_sandbox_task="GPU",
    )
    assert adapter.resolve_turn_settings({"RSAW_TASK_ID": "GPU"}) == {
        "task": "GPU",
        "sandbox": "danger-full-access",
        "source": "CLI task override",
    }
    assert adapter.resolve_turn_settings({"RSAW_TASK_ID": "ANALYST"}) == {
        "task": "ANALYST",
        "sandbox": "workspace-write",
        "source": "default",
    }


def test_tui_tracks_resolved_sandbox(tmp_path: Path) -> None:
    dashboard = LiveDashboardV6(tmp_path)
    dashboard.handle_supervisor_event(
        {
            "type": "v7.sandbox.resolved",
            "task": "GPU",
            "sandbox": "danger-full-access",
            "source": "task override",
        }
    )
    assert dashboard._state["sandbox"] == "danger-full-access"
    assert dashboard._state["sandbox_source"] == "task override"


def test_operator_reasons_reject_whitespace(tmp_path: Path) -> None:
    _repo(tmp_path)
    with pytest.raises(SystemExit):
        cli_main(
            [
                "sandbox",
                "set",
                str(tmp_path),
                "--mode",
                "danger-full-access",
                "--reason",
                "   ",
                "--yes",
            ]
        )
    with pytest.raises(SystemExit):
        cli_main(
            [
                "gate",
                "clear",
                str(tmp_path),
                "--reason",
                "\t",
                "--yes",
            ]
        )


def test_verify_detects_operator_action_tampering(tmp_path: Path, capsys) -> None:
    _repo(tmp_path)
    assert (
        cli_main(
            [
                "sandbox",
                "set",
                str(tmp_path),
                "--mode",
                "danger-full-access",
                "--reason",
                "reviewed GPU boundary",
                "--yes",
                "--json",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    audit_path = tmp_path / payload["audit"]
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["reason"] = "tampered"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    result = cli_module.verify_repository(tmp_path)
    assert not result.ok
    assert any("Operator action checksum mismatch" in error for error in result.errors)
