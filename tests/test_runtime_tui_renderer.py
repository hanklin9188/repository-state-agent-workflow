from __future__ import annotations

from pathlib import Path

from repo_state_agent.runtime.tui.live import should_use_tui
from repo_state_agent.runtime.tui.model import DashboardModel
from repo_state_agent.runtime.tui.renderer import render_dashboard_text


def _write_repository(root: Path) -> None:
    (root / "docs/tasks").mkdir(parents=True, exist_ok=True)
    (root / "docs/workstreams").mkdir(parents=True, exist_ok=True)
    (root / "AGENTS.md").write_text("# Policy\n", encoding="utf-8")
    (root / "docs/workstreams/W-1.md").write_text(
        """# W-1 — EdgeFlow Core

## State Machine

```text
Design → Implement → Validate → Run → Analyze
```
""",
        encoding="utf-8",
    )
    (root / "docs/tasks/T-1.md").write_text(
        "# T-1 — GPU Observability Diagnostic\n", encoding="utf-8"
    )
    (root / "docs/tasks/T-2.md").write_text("# T-2 — Formal Execution\n", encoding="utf-8")
    (root / "ACTIVE.md").write_text(
        """# Active Handoff

## Workstream
ID: W-1
Spec: docs/workstreams/W-1.md

## Context Epoch
ID: E-3
Role: Builder

## Active Task
ID: T-1
Spec: docs/tasks/T-1.md

## Required Reads
- AGENTS.md
- ACTIVE.md
- docs/tasks/T-1.md

## Human Gate
None.

## Next Exact Action
Run focused validation.

## Stop Condition
Checkpoint accepted.

## Continuation Gate
Decision: CONTINUE_ALLOWED
Reason: TIGHTLY_COUPLED_TASK

## Next Task
ID: T-2
Spec: docs/tasks/T-2.md

## Next Session Role
Builder

## Recommended Reasoning
Medium
""",
        encoding="utf-8",
    )


def _working_model(root: Path) -> DashboardModel:
    _write_repository(root)
    model = DashboardModel(root, rotate_input_tokens=60_000)
    model.handle_supervisor_event(
        {"type": "runtime_epoch_started", "runtime_epoch": 3, "reason": "test"}
    )
    model.handle_supervisor_event({"type": "agent_turn_started", "turn": 6, "mode": "continue"})
    model.handle_codex_event(
        {
            "type": "item.started",
            "item": {
                "type": "command_execution",
                "command": "pytest tests/test_gpu_observer.py",
            },
        }
    )
    model.handle_codex_event(
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 41_200,
                "cached_input_tokens": 34_800,
                "output_tokens": 2_100,
            },
        }
    )
    model.handle_supervisor_event(
        {
            "type": "agent_turn_terminal",
            "ok": True,
            "usage": {
                "input_tokens": 41_200,
                "cached_input_tokens": 34_800,
                "output_tokens": 2_100,
            },
            "latest_turn_usage": {
                "input_tokens": 41_200,
                "cached_input_tokens": 34_800,
                "output_tokens": 2_100,
            },
        }
    )
    model.handle_supervisor_event({"type": "checkpoint_observed", "checkpoint": 6})
    return model


def test_expanded_dashboard_answers_operator_questions(tmp_path: Path) -> None:
    text = render_dashboard_text(_working_model(tmp_path).snapshot(), width=110, compact=False)
    assert "RSAW · EdgeFlow Core" in text
    assert "GPU Observability Diagnostic" in text
    assert "Validate" in text
    assert "Checkpoint" in text and "6" in text
    assert "CONTINUE · same context" in text
    assert "CONTEXT PRESSURE" in text
    assert "Cached" in text and "Fresh" in text
    assert "RECENT" in text
    assert "Gate NONE" in text
    assert "private detailed reasoning" not in text


def test_compact_dashboard_survives_narrow_terminal(tmp_path: Path) -> None:
    text = render_dashboard_text(_working_model(tmp_path).snapshot(), width=72, compact=True)
    assert "NOW" in text
    assert "Checkpoint 6" in text
    assert "Fresh 6.4k" in text
    assert max(len(line) for line in text.splitlines()) <= 72


def test_pause_failed_and_complete_views_are_unambiguous(tmp_path: Path) -> None:
    model = _working_model(tmp_path)
    model.handle_supervisor_event(
        {
            "type": "transition",
            "action": "PAUSE",
            "reasons": ["HUMAN_GATE"],
            "human_gate": "FORMAL_AUTHORIZATION",
        }
    )
    paused = render_dashboard_text(model.snapshot(), width=90)
    assert "ACTION REQUIRED" in paused
    assert "FORMAL_AUTHORIZATION" in paused

    model.finalize(status="FAILED", reason="AGENT_TURN_FAILED", summary_path="summary.json")
    failed = render_dashboard_text(model.snapshot(), width=90)
    assert "SUPERVISOR STOPPED" in failed
    assert "AGENT_TURN_FAILED" in failed
    assert "summary.json" in failed

    model.finalize(
        status="COMPLETE",
        reason="WORKSTREAM_COMPLETE",
        summary_path="summary.json",
        summary={
            "runtime_epochs": 4,
            "agent_turns": 7,
            "checkpoints_observed": 7,
            "total_usage": {
                "input_tokens": 100_000,
                "cached_input_tokens": 80_000,
                "output_tokens": 5_000,
            },
        },
    )
    complete = render_dashboard_text(model.snapshot(), width=90)
    assert "WORKSTREAM COMPLETE" in complete
    assert "Context epochs" in complete
    assert "Fresh" in complete


def test_tui_auto_detection_preserves_non_tty_output(monkeypatch) -> None:
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("TERM", "xterm-256color")
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    assert should_use_tui()
    assert not should_use_tui(disable=True)
    assert not should_use_tui(json_output=True)
    assert not should_use_tui(quiet=True)
    assert not should_use_tui(dry_run=True)

    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    assert not should_use_tui()
    assert should_use_tui(force=True)
