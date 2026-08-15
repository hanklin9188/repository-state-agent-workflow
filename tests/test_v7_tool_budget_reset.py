from __future__ import annotations

from repo_state_agent.runtime.codex import _reset_bound_guard
from repo_state_agent.runtime.tool_budget import ToolBudget, ToolBudgetGuard


def _started(identifier: str) -> dict[str, object]:
    return {
        "type": "item.started",
        "item": {
            "id": identifier,
            "type": "command_execution",
            "command": f"printf {identifier}",
        },
    }


def test_bound_tool_budget_is_reset_between_codex_turns() -> None:
    guard = ToolBudgetGuard(
        ToolBudget(
            max_tool_calls_per_turn=1,
            max_tool_output_tokens=100,
            max_single_tool_output_tokens=100,
            max_broad_discovery_commands=1,
            enforce=True,
        )
    )

    assert guard.observe(_started("turn-1-tool-1")) is None
    assert guard.observe(_started("turn-1-tool-2")) == "MAX_TOOL_CALLS:2>1"

    _reset_bound_guard(guard.observe)

    assert guard.snapshot().tool_calls == 0
    assert guard.snapshot().violation == ""
    assert guard.observe(_started("turn-2-tool-1")) is None
