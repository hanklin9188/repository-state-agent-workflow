from __future__ import annotations

from repo_state_agent.runtime.report import efficiency_view


def test_efficiency_view_reports_context_cost_per_checkpoint() -> None:
    view = efficiency_view(
        {
            "run_id": "r1",
            "status": "COMPLETE",
            "reason": "WORKSTREAM_COMPLETE",
            "workstream": "W-1",
            "agent_turns": 4,
            "runtime_epochs": 2,
            "fresh_turns": 2,
            "resumed_turns": 2,
            "checkpoints_observed": 4,
            "transitions": {"CONTINUE": 2, "ROTATE": 2, "COMPLETE": 1},
            "total_usage": {
                "input_tokens": 1000,
                "cached_input_tokens": 600,
                "output_tokens": 100,
            },
        }
    )
    assert view["input_tokens_per_checkpoint"] == 250.0
    assert view["fresh_input_tokens"] == 400
    assert view["fresh_input_tokens_per_checkpoint"] == 100.0
    assert view["cache_reuse_ratio"] == 0.6
    assert view["context_efficiency"]["rotations"] == 2
    assert view["runtime_epochs"] == 2
