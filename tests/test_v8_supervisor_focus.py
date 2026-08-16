from __future__ import annotations

import json
import subprocess
from pathlib import Path

from repo_state_agent.runtime.model import AdapterDoctorResult, AgentTurnResult, TokenUsage
from repo_state_agent.runtime.v6 import V6Options, supervise_v6


def _repo(root: Path) -> None:
    subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    (root / "docs/tasks").mkdir(parents=True)
    (root / "docs/workstreams").mkdir(parents=True)
    (root / "src").mkdir()
    (root / ".rsaw").mkdir()
    (root / "AGENTS.md").write_text("# Policy\n")
    (root / "docs/workstreams/W.md").write_text("# W\n")
    (root / "docs/tasks/T.md").write_text(
        """# Repair parser

Update `src/parser.py` function `parse_packet`.

## Allowed Writes
- src/parser.py

## Validation
- `python -m pytest -q`
"""
    )
    (root / "src/parser.py").write_text("def parse_packet(payload):\n    return payload.strip()\n")
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
                "schema_version": 5,
                "runtime": {
                    "max_transitions": 2,
                    "v6": {"enabled": True},
                    "relevance": {
                        "enabled": True,
                        "mapTokens": 400,
                        "focusTokens": 800,
                        "maxSnippets": 3,
                        "candidateLimit": 8,
                    },
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


def _payload(complete: bool) -> dict[str, object]:
    return {
        "schemaVersion": "rsaw.checkpoint-result.v1",
        "outcome": "COMPLETE" if complete else "PASS",
        "summary": "parser checked",
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
            "nextAction": "finish" if complete else "continue",
        },
        "nextTask": (
            None if complete else {"id": "T", "spec": "docs/tasks/T.md", "role": "Builder"}
        ),
        "followingTask": None,
        "nextAction": "finish" if complete else "continue",
        "stopCondition": "complete",
        "requestedAction": "COMPLETE" if complete else "CONTINUE",
        "transitionReason": "done" if complete else "same task",
        "humanGate": "",
    }


class _Adapter:
    name = "fake"

    def __init__(self, first_usage: TokenUsage | None = None) -> None:
        self.prompts: list[str] = []
        self.threads: list[str | None] = []
        self.first_usage = first_usage

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
        self.prompts.append(prompt)
        self.threads.append(thread_id)
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
            + "\n"
        )
        message = json.dumps(_payload(turn_index == 2))
        last = run_dir / f"turn-{turn_index:04d}-last-message.txt"
        last.write_text(message)
        usage = (
            self.first_usage
            if turn_index == 1 and self.first_usage is not None
            else TokenUsage(input_tokens=100)
        )
        return AgentTurnResult(
            exit_code=0,
            thread_id="thread-1",
            usage=usage,
            latest_turn_usage=usage,
            last_message=message,
            events_path=events,
            last_message_path=last,
        )


def test_supervisor_injects_focus_once_and_reuses_it_on_continue(tmp_path: Path) -> None:
    _repo(tmp_path)
    adapter = _Adapter()

    result = supervise_v6(tmp_path, adapter, V6Options(max_transitions=2))

    assert result.status == "COMPLETE"
    assert len(adapter.prompts) == 2
    assert "## RSAW Focus Context" in adapter.prompts[0]
    assert "src/parser.py" in adapter.prompts[0]
    assert "## RSAW Focus Context" not in adapter.prompts[1]
    summary = json.loads(result.summary_path.read_text())
    assert summary["focus_builds"] == 1
    assert summary["focus_reuses"] == 1
    assert summary["focus_snippets"] >= 1
    assert summary["focus_context_tokens"] > 0


def test_continue_envelope_references_unchanged_task_and_focus(tmp_path: Path) -> None:
    _repo(tmp_path)
    adapter = _Adapter()

    result = supervise_v6(tmp_path, adapter, V6Options(max_transitions=2))

    assert result.status == "COMPLETE"
    run_dir = result.summary_path.parent
    second = json.loads(
        (run_dir / "../../state/envelopes" / result.run_id / "turn-0002.json").resolve().read_text()
    )
    by_name = {component["name"]: component for component in second["components"]}
    assert by_name["Task contract"]["category"] == "exact-ref"
    assert by_name["Focus context"]["category"] == "focus-ref"
    assert second["reusedReferenceTokens"] > 0


def test_provider_traffic_pressure_compacts_before_next_turn(tmp_path: Path) -> None:
    _repo(tmp_path)
    config_path = tmp_path / ".rsaw/config.json"
    config = json.loads(config_path.read_text())
    config["runtime"]["relevance"].update(
        {
            "maxProviderInputTokens": 500,
            "maxCachedInputTokens": 300,
        }
    )
    config_path.write_text(json.dumps(config) + "\n")
    adapter = _Adapter(TokenUsage(input_tokens=900, cached_input_tokens=700))

    result = supervise_v6(tmp_path, adapter, V6Options(max_transitions=2))

    assert result.status == "COMPLETE"
    assert adapter.threads == [None, None]
    summary = json.loads(result.summary_path.read_text())
    assert summary["provider_pressure_compactions"] == 1
    assert summary["context_compactions"] == 1
    assert summary["focus_builds"] == 2
