from __future__ import annotations

from pathlib import Path

from repo_state_agent.runtime.model import (
    AdapterDoctorResult,
    AgentTurnResult,
    TokenUsage,
)
from repo_state_agent.runtime.supervisor import SupervisorOptions, supervise


def _write_repo(root: Path, *, continuation: str, task: str, next_task: str) -> None:
    (root / "docs/tasks").mkdir(parents=True, exist_ok=True)
    (root / "docs/workstreams").mkdir(parents=True, exist_ok=True)
    (root / "AGENTS.md").write_text("# Policy\n", encoding="utf-8")
    (root / "docs/workstreams/W-1.md").write_text("# W-1 — Demo\n", encoding="utf-8")
    (root / f"docs/tasks/{task}.md").write_text(f"# {task}\n", encoding="utf-8")
    (root / f"docs/tasks/{next_task}.md").write_text(
        f"# {next_task}\n", encoding="utf-8"
    )
    (root / "ACTIVE.md").write_text(
        f"""# Active Handoff

## Workstream
ID: W-1
Spec: docs/workstreams/W-1.md

## Context Epoch
ID: E-1
Role: Builder

## Active Task
ID: {task}
Spec: docs/tasks/{task}.md

## Required Reads
- AGENTS.md
- ACTIVE.md
- docs/tasks/{task}.md

## Human Gate
None.

## Next Exact Action
Do the task.

## Stop Condition
Checkpoint accepted.

## Continuation Gate
Decision: {continuation}
Reason: TEST

## Next Task
ID: {next_task}
Spec: docs/tasks/{next_task}.md

## Next Session Role
Builder

## Recommended Reasoning
Medium
""",
        encoding="utf-8",
    )


class FakeAdapter:
    name = "fake"

    def __init__(self, root: Path) -> None:
        self.root = root

    def doctor(self) -> AdapterDoctorResult:
        return AdapterDoctorResult(True, "fake", "fake", "1")

    def run_turn(self, **_: object) -> AgentTurnResult:
        _write_repo(
            self.root,
            continuation="COMPLETE",
            task="T-2",
            next_task="T-3",
        )
        return AgentTurnResult(
            exit_code=0,
            thread_id="thread-1",
            usage=TokenUsage(input_tokens=100, cached_input_tokens=80),
            latest_turn_usage=TokenUsage(input_tokens=100, cached_input_tokens=80),
        )


def test_supervisor_emits_presentation_events_without_changing_lifecycle(
    tmp_path: Path,
) -> None:
    _write_repo(
        tmp_path,
        continuation="ROTATE_REQUIRED",
        task="T-1",
        next_task="T-2",
    )
    events: list[dict[str, object]] = []
    result = supervise(
        tmp_path,
        FakeAdapter(tmp_path),
        SupervisorOptions(quiet=True),
        event_sink=events.append,
    )
    assert result.status == "COMPLETE"
    event_types = [event["type"] for event in events]
    assert "supervisor_started" in event_types
    assert "agent_turn_started" in event_types
    assert "repository_verification_passed" in event_types
    assert "checkpoint_observed" in event_types
    assert event_types[-1] == "supervisor_terminal"


def test_presentation_sink_failure_is_isolated(tmp_path: Path) -> None:
    _write_repo(
        tmp_path,
        continuation="ROTATE_REQUIRED",
        task="T-1",
        next_task="T-2",
    )

    def broken_sink(_: dict[str, object]) -> None:
        raise RuntimeError("TUI failed")

    result = supervise(
        tmp_path,
        FakeAdapter(tmp_path),
        SupervisorOptions(quiet=True),
        event_sink=broken_sink,
    )
    assert result.status == "COMPLETE"
