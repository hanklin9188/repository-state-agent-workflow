from __future__ import annotations

import hashlib
import json
from pathlib import Path

from rich.console import Console

import repo_state_agent.runtime.v6 as v6
from repo_state_agent.active_format import canonicalize_active_text
from repo_state_agent.model import ActiveState
from repo_state_agent.parsing import parse_active
from repo_state_agent.runtime.model import AdapterDoctorResult, AgentTurnResult, TokenUsage
from repo_state_agent.runtime.tool_budget import ToolBudget, ToolBudgetGuard
from repo_state_agent.runtime.tui.v6 import LiveDashboardV6
from repo_state_agent.runtime.v6 import (
    CheckpointResult,
    GateDecision,
    GovernorDecision,
    SemanticCapsule,
    TaskRef,
    V6Options,
    deterministic_gate,
    inspect_turn_events,
    migrate_v7,
    supervise_v6,
)
from repo_state_agent.v7_cli import main as cli_main
from repo_state_agent.verify import VerificationResult, verify_repository


def _repo(root: Path) -> None:
    (root / ".rsaw/state/checkpoints").mkdir(parents=True, exist_ok=True)
    (root / "docs/tasks").mkdir(parents=True, exist_ok=True)
    (root / "docs/workstreams").mkdir(parents=True, exist_ok=True)
    (root / "AGENTS.md").write_text(
        "# Policy\nRepository state is authoritative.\n",
        encoding="utf-8",
    )
    (root / "docs/workstreams/W.md").write_text("# W\n", encoding="utf-8")
    (root / "docs/tasks/T1.md").write_text(
        """# T1

## Allowed Writes
- src/**
- tests/**

## Validation
- `python -m pytest -q`
""",
        encoding="utf-8",
    )
    (root / "docs/tasks/T2.md").write_text("# T2\n", encoding="utf-8")
    (root / "docs/tasks/T3.md").write_text("# T3\n", encoding="utf-8")
    (root / "ACTIVE.md").write_text(
        """# Active Handoff

## Workstream
ID: W
Spec: docs/workstreams/W.md

## Context Epoch
ID: E-1
Role: Builder

## Active Task
ID: T1
Spec: docs/tasks/T1.md

## Required Reads
- AGENTS.md
- ACTIVE.md
- docs/tasks/T1.md

## Human Gate
None.

## Next Exact Action
Implement the scoped change.

## Stop Condition
Focused validation passes.

## Continuation Gate
Decision: ROTATE_REQUIRED
Reason: independent review boundary

## Next Task
ID: T2
Spec: docs/tasks/T2.md

## Next Session Role
Reviewer

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
                    "max_total_input_tokens": 5_000_000,
                    "v6": {"enabled": True},
                    "codex": {
                        "binary": "codex",
                        "defaultSandbox": "workspace-write",
                        "taskSandboxOverrides": {},
                    },
                    "toolBudget": {
                        "maxToolCallsPerTurn": 32,
                        "maxToolOutputTokens": 50_000,
                        "maxSingleToolOutputTokens": 20_000,
                        "maxBroadDiscoveryCommands": 2,
                        "enforce": True,
                    },
                },
            }
        ),
        encoding="utf-8",
    )


def _result_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schemaVersion": v6.SCHEMA_RESULT,
        "outcome": "PASS",
        "summary": "implementation complete",
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
            "nextAction": "review",
        },
        "nextTask": {"id": "T2", "spec": "docs/tasks/T2.md", "role": "Reviewer"},
        "followingTask": {"id": "T3", "spec": "docs/tasks/T3.md", "role": "Builder"},
        "nextAction": "Review the sealed change.",
        "stopCondition": "Independent review completes.",
        "requestedAction": "ROTATE",
        "transitionReason": "builder to reviewer",
        "humanGate": "",
    }
    payload.update(overrides)
    return payload


def _result(**overrides: object) -> CheckpointResult:
    return CheckpointResult.parse(json.dumps(_result_payload(**overrides)))


def test_task_ref_accepts_snake_case_from_real_codex_output() -> None:
    result = _result(
        nextTask={
            "task_id": "E04-ANALYSIS",
            "task_spec": "docs/tasks/T2.md",
            "role": "Analyst",
        }
    )
    assert result.next_task == TaskRef("E04-ANALYSIS", "docs/tasks/T2.md", "Analyst")


def test_model_source_evidence_refs_are_hints_not_authority(tmp_path: Path) -> None:
    _repo(tmp_path)
    state = parse_active(tmp_path)
    before = hashlib.sha256((tmp_path / "ACTIVE.md").read_bytes()).hexdigest()
    delta = dict(_result_payload()["semanticCapsuleDelta"])
    delta["evidenceRefs"] = ["ACTIVE.md", "docs/tasks/T1.md"]
    gate = deterministic_gate(
        tmp_path,
        state=state,
        result=_result(semanticCapsuleDelta=delta),
        active_sha_before=before,
        changed_files=(),
        event_info={
            "commands": [
                {
                    "command": "python -m pytest -q",
                    "eventType": "item.completed",
                    "exitCode": 0,
                }
            ]
        },
        evidence_ids=set(),
    )
    assert gate.accepted
    assert "MODEL_SOURCE_REFS_IGNORED:SUPERVISOR_OWNS_EVIDENCE_BINDING" in gate.warnings


def test_claimed_ev_handle_remains_strict(tmp_path: Path) -> None:
    _repo(tmp_path)
    state = parse_active(tmp_path)
    before = hashlib.sha256((tmp_path / "ACTIVE.md").read_bytes()).hexdigest()
    delta = dict(_result_payload()["semanticCapsuleDelta"])
    delta["evidenceRefs"] = ["EV-FILE-not-observed"]
    gate = deterministic_gate(
        tmp_path,
        state=state,
        result=_result(semanticCapsuleDelta=delta),
        active_sha_before=before,
        changed_files=(),
        event_info={
            "commands": [
                {
                    "command": "python -m pytest -q",
                    "eventType": "item.completed",
                    "exitCode": 0,
                }
            ]
        },
        evidence_ids=set(),
    )
    assert not gate.accepted
    assert "UNKNOWN_EVIDENCE_REFS:EV-FILE-not-observed" in gate.errors


def test_capsule_persists_only_supervisor_bound_evidence() -> None:
    capsule = SemanticCapsule("W")
    capsule.merge(
        {"evidenceRefs": ["ACTIVE.md", "docs/tasks/T1.md"]},
        checkpoint_id="CP-0001",
        revision="abc",
        role="Builder",
        objective="test",
        evidence_refs=["EV-FILE-authoritative"],
        max_tokens=2500,
    )
    assert capsule.evidence_refs == ["EV-FILE-authoritative"]


def test_turn_event_inspection_deduplicates_started_and_completed(tmp_path: Path) -> None:
    events = tmp_path / "events.jsonl"
    events.write_text(
        "\n".join(
            json.dumps(row)
            for row in (
                {
                    "type": "item.started",
                    "item": {
                        "id": "cmd-1",
                        "type": "command_execution",
                        "command": "rg --files",
                    },
                },
                {
                    "type": "item.completed",
                    "item": {
                        "id": "cmd-1",
                        "type": "command_execution",
                        "command": "rg --files",
                        "aggregated_output": "a.py\nb.py\n",
                        "exit_code": 0,
                    },
                },
            )
        )
        + "\n",
        encoding="utf-8",
    )
    info = inspect_turn_events(
        AgentTurnResult(exit_code=0, thread_id="t", events_path=events),
        tmp_path,
    )
    assert info["tool_calls"] == 1
    assert len(info["commands"]) == 1
    assert info["commands"][0]["exitCode"] == 0
    assert info["broad_discovery_commands"] == 1


def test_tool_budget_stops_large_tool_output() -> None:
    guard = ToolBudgetGuard(
        ToolBudget(
            max_tool_calls_per_turn=10,
            max_tool_output_tokens=10,
            max_single_tool_output_tokens=8,
            max_broad_discovery_commands=2,
            enforce=True,
        )
    )
    assert (
        guard.observe(
            {
                "type": "item.started",
                "item": {
                    "id": "cmd-1",
                    "type": "command_execution",
                    "command": "sed -n '1,200p' file",
                },
            }
        )
        is None
    )
    violation = guard.observe(
        {
            "type": "item.completed",
            "item": {
                "id": "cmd-1",
                "type": "command_execution",
                "command": "sed -n '1,200p' file",
                "aggregated_output": "x" * 40,
                "exit_code": 0,
            },
        }
    )
    assert violation == "MAX_SINGLE_TOOL_OUTPUT_TOKENS:10>8"


def test_active_format_does_not_inflate_over_many_advances(tmp_path: Path) -> None:
    _repo(tmp_path)
    state = parse_active(tmp_path)
    decision = GovernorDecision("ROTATE", "ROLE_BOUNDARY", 0.1, 1000)
    result = _result()
    for index in range(1, 65):
        text = v6._render_active_markdown(
            tmp_path,
            state,
            result,
            decision,
            f"CP-{index:04d}",
        )
        (tmp_path / "ACTIVE.md").write_text(text, encoding="utf-8")
    final = (tmp_path / "ACTIVE.md").read_text(encoding="utf-8")
    assert final == canonicalize_active_text(final)
    assert len(final.splitlines()) <= 140
    assert "\n\n\n" not in final


def test_verify_uses_canonical_budget_not_raw_blank_line_count(tmp_path: Path) -> None:
    _repo(tmp_path)
    path = tmp_path / "ACTIVE.md"
    path.write_text(path.read_text() + "\n" * 200, encoding="utf-8")
    result = verify_repository(tmp_path)
    assert result.ok
    assert any("not canonical" in warning for warning in result.warnings)


def test_dashboard_loads_repository_global_checkpoint(tmp_path: Path) -> None:
    _repo(tmp_path)
    (tmp_path / ".rsaw/state/checkpoints/CP-0042.json").write_text(
        "{}", encoding="utf-8"
    )
    dashboard = LiveDashboardV6(tmp_path, console=Console(record=True))
    assert dashboard._state["checkpoint"] == 42
    assert dashboard._state["task"] == "T1"


def test_v07_migration_adds_operator_profiles_and_budgets(tmp_path: Path) -> None:
    _repo(tmp_path)
    before = (tmp_path / "ACTIVE.md").read_bytes()
    result = migrate_v7(tmp_path, apply=True)
    assert result["status"] == "MIGRATED"
    assert (tmp_path / "ACTIVE.md").read_bytes() == before
    config = json.loads((tmp_path / ".rsaw/config.json").read_text())
    assert config["schema_version"] == 4
    assert config["runtime"]["codex"]["defaultSandbox"] == "workspace-write"
    assert config["runtime"]["toolBudget"]["enforce"] is True


class _FakeAdapter:
    name = "fake"

    def doctor(self) -> AdapterDoctorResult:
        return AdapterDoctorResult(ok=True, adapter="fake", binary="fake")

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
        events = run_dir / f"turn-{turn_index:04d}.jsonl"
        events.write_text(
            "\n".join(
                json.dumps(row)
                for row in (
                    {
                        "type": "item.started",
                        "item": {
                            "id": "cmd-1",
                            "type": "command_execution",
                            "command": "python -m pytest -q",
                        },
                    },
                    {
                        "type": "item.completed",
                        "item": {
                            "id": "cmd-1",
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
        message = json.dumps(_result_payload())
        last = run_dir / f"turn-{turn_index:04d}-last-message.txt"
        last.write_text(message, encoding="utf-8")
        return AgentTurnResult(
            exit_code=0,
            thread_id="thread-1",
            usage=TokenUsage(input_tokens=100, cached_input_tokens=50),
            latest_turn_usage=TokenUsage(input_tokens=100, cached_input_tokens=50),
            last_message=message,
            events_path=events,
            last_message_path=last,
        )


def test_post_advance_failure_rolls_back_all_authority_files(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _repo(tmp_path)
    active_before = (tmp_path / "ACTIVE.md").read_bytes()
    calls = 0

    def verification(_root: Path) -> VerificationResult:
        nonlocal calls
        calls += 1
        if calls == 1:
            return VerificationResult()
        return VerificationResult(errors=["synthetic post-advance failure"])

    monkeypatch.setattr(v6, "verify_repository", verification)
    result = supervise_v6(
        tmp_path,
        _FakeAdapter(),
        V6Options(max_transitions=1),
    )
    assert result.exit_code == 23
    assert "POST_ADVANCE_REPOSITORY_INVALID" in result.reason
    assert (tmp_path / "ACTIVE.md").read_bytes() == active_before
    assert not (tmp_path / ".rsaw/state/checkpoints/CP-0001.json").exists()
    assert not (tmp_path / ".rsaw/state/active.json").exists()
    assert not (tmp_path / ".rsaw/state/capsules/W.json").exists()


def test_gate_clear_is_atomic_and_audited(tmp_path: Path, capsys) -> None:
    _repo(tmp_path)
    active = (tmp_path / "ACTIVE.md").read_text()
    active = active.replace("## Human Gate\nNone.", "## Human Gate\nGPU access required")
    active = active.replace(
        "Decision: ROTATE_REQUIRED\nReason: independent review boundary",
        "Decision: STOP_REQUIRED\nReason: HUMAN_GATE",
    )
    (tmp_path / "ACTIVE.md").write_text(active, encoding="utf-8")
    rc = cli_main(
        [
            "gate",
            "clear",
            str(tmp_path),
            "--reason",
            "GPU access restored",
            "--yes",
            "--json",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "CLEARED"
    state = parse_active(tmp_path)
    assert state.human_gate == ""
    assert state.continuation == "ROTATE_REQUIRED"
    assert (tmp_path / payload["audit"]).is_file()


def test_top_level_help_surfaces_daily_commands(capsys) -> None:
    assert cli_main(["--help"]) == 0
    output = capsys.readouterr().out
    assert "rsaw start" in output
    assert "rsaw preflight" in output
    assert "rsaw gate clear" in output
    assert "rsaw sandbox set" in output
