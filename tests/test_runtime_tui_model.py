from __future__ import annotations

from pathlib import Path

from repo_state_agent.runtime.tui.model import DashboardModel


def _write_repository(root: Path, *, continuation: str = "CONTINUE_ALLOWED") -> None:
    (root / "docs/tasks").mkdir(parents=True, exist_ok=True)
    (root / "docs/workstreams").mkdir(parents=True, exist_ok=True)
    (root / "AGENTS.md").write_text("# Policy\n", encoding="utf-8")
    (root / "docs/workstreams/W-1.md").write_text(
        """# W-1 — Runtime Delivery

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
        f"""# Active Handoff

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
Decision: {continuation}
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


def test_dashboard_model_tracks_repository_activity_and_token_cost(tmp_path: Path) -> None:
    _write_repository(tmp_path)
    model = DashboardModel(tmp_path, rotate_input_tokens=60_000)
    model.handle_supervisor_event(
        {
            "type": "supervisor_started",
            "run_id": "run-1",
            "rotate_input_tokens": 60_000,
        }
    )
    model.handle_supervisor_event(
        {"type": "runtime_epoch_started", "runtime_epoch": 3, "reason": "test"}
    )
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

    snapshot = model.snapshot()
    assert snapshot.workstream_title == "Runtime Delivery"
    assert snapshot.task_title == "GPU Observability Diagnostic"
    assert snapshot.current_stage == 2
    assert snapshot.checkpoints_observed == 6
    assert snapshot.fresh_input_tokens == 6_400
    assert snapshot.cache_ratio == 34_800 / 41_200
    assert snapshot.context_pressure == 41_200 / 60_000
    assert snapshot.total_usage.input_tokens == 41_200


def test_reasoning_events_never_render_hidden_reasoning_content(tmp_path: Path) -> None:
    _write_repository(tmp_path)
    model = DashboardModel(tmp_path, rotate_input_tokens=60_000)
    model.handle_codex_event(
        {
            "type": "item.started",
            "item": {
                "type": "reasoning",
                "text": "private detailed reasoning must not be shown",
            },
        }
    )

    activity = model.snapshot().current_activity
    assert activity.title == "Analyzing repository state"
    assert activity.detail == ""


def test_rotation_and_pause_are_derived_from_runtime_events(tmp_path: Path) -> None:
    _write_repository(tmp_path, continuation="ROTATE_REQUIRED")
    model = DashboardModel(tmp_path, rotate_input_tokens=60_000)
    model.handle_supervisor_event(
        {"type": "runtime_epoch_started", "runtime_epoch": 2, "reason": "test"}
    )
    model.handle_supervisor_event(
        {
            "type": "transition",
            "action": "ROTATE",
            "reasons": ["ROLE_BOUNDARY"],
        }
    )
    rotating = model.snapshot()
    assert rotating.status == "ROTATING"
    assert rotating.next_action == "ROTATE"
    assert rotating.transition_reason == "ROLE_BOUNDARY"

    model.handle_supervisor_event(
        {
            "type": "transition",
            "action": "PAUSE",
            "reasons": ["HUMAN_GATE"],
            "human_gate": "FORMAL_AUTHORIZATION",
        }
    )
    paused = model.snapshot()
    assert paused.status == "PAUSED"
    assert paused.human_gate == "FORMAL_AUTHORIZATION"
