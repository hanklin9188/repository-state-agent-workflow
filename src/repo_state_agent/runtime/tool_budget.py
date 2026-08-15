from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any

_TOOL_TYPES = {
    "command_execution",
    "command",
    "shell",
    "shell_command",
    "tool_call",
    "mcp_tool_call",
    "function_call",
}

_BROAD_DISCOVERY_PATTERNS = (
    re.compile(r"(?:^|\s)rg\s+--files(?:\s|$)"),
    re.compile(r"(?:^|\s)find\s+\.?(?:\s|$)"),
    re.compile(r"(?:^|\s)git\s+ls-files(?:\s|$)"),
    re.compile(r"(?:^|\s)tree(?:\s|$)"),
)


@dataclass(frozen=True)
class ToolBudget:
    max_tool_calls_per_turn: int = 32
    max_tool_output_tokens: int = 50_000
    max_single_tool_output_tokens: int = 20_000
    max_broad_discovery_commands: int = 2
    enforce: bool = True


@dataclass(frozen=True)
class ToolBudgetSnapshot:
    tool_calls: int
    tool_output_tokens: int
    peak_tool_output_tokens: int
    broad_discovery_commands: int
    violation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ToolBudgetGuard:
    """Observe one Codex turn and stop a runaway tool loop deterministically."""

    def __init__(
        self,
        budget: ToolBudget,
        *,
        event_sink: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.budget = budget
        self.event_sink = event_sink
        self.reset()

    def reset(self) -> None:
        """Begin a new per-turn accounting window."""

        self._started: set[str] = set()
        self._completed: set[str] = set()
        self._broad: set[str] = set()
        self._tool_calls = 0
        self._tool_output_tokens = 0
        self._peak_tool_output_tokens = 0
        self._violation = ""

    def observe(self, event: dict[str, Any]) -> str | None:
        if self._violation:
            return self._violation

        payload = event.get("item") if isinstance(event.get("item"), dict) else event
        event_type = str(event.get("type") or "")
        item_type = str(payload.get("type") or "").lower()
        command = _command(payload)
        identity = str(payload.get("id") or event.get("id") or command or item_type)

        if (
            item_type in _TOOL_TYPES
            and event_type.endswith(".started")
            and identity not in self._started
        ):
            self._started.add(identity)
            self._tool_calls += 1
            if command and is_broad_discovery(command):
                self._broad.add(identity)

        if (
            item_type in _TOOL_TYPES
            and event_type.endswith(".completed")
            and identity not in self._completed
        ):
            self._completed.add(identity)
            output = _output(payload)
            output_tokens = _tokens(output)
            self._tool_output_tokens += output_tokens
            self._peak_tool_output_tokens = max(
                self._peak_tool_output_tokens,
                output_tokens,
            )

        violation = self._check()
        if violation:
            self._violation = violation
            self._emit()
            return violation
        return None

    def snapshot(self) -> ToolBudgetSnapshot:
        return ToolBudgetSnapshot(
            tool_calls=self._tool_calls,
            tool_output_tokens=self._tool_output_tokens,
            peak_tool_output_tokens=self._peak_tool_output_tokens,
            broad_discovery_commands=len(self._broad),
            violation=self._violation,
        )

    def _check(self) -> str:
        if not self.budget.enforce:
            return ""
        if self._tool_calls > self.budget.max_tool_calls_per_turn:
            return (
                "MAX_TOOL_CALLS:"
                f"{self._tool_calls}>{self.budget.max_tool_calls_per_turn}"
            )
        if self._peak_tool_output_tokens > self.budget.max_single_tool_output_tokens:
            return (
                "MAX_SINGLE_TOOL_OUTPUT_TOKENS:"
                f"{self._peak_tool_output_tokens}>"
                f"{self.budget.max_single_tool_output_tokens}"
            )
        if self._tool_output_tokens > self.budget.max_tool_output_tokens:
            return (
                "MAX_TOOL_OUTPUT_TOKENS:"
                f"{self._tool_output_tokens}>{self.budget.max_tool_output_tokens}"
            )
        if len(self._broad) > self.budget.max_broad_discovery_commands:
            return (
                "MAX_BROAD_DISCOVERY_COMMANDS:"
                f"{len(self._broad)}>"
                f"{self.budget.max_broad_discovery_commands}"
            )
        return ""

    def _emit(self) -> None:
        if self.event_sink is None:
            return
        try:
            self.event_sink(
                {
                    "type": "rsaw.tool-budget.exceeded",
                    **self.snapshot().to_dict(),
                }
            )
        except Exception:
            return


def is_broad_discovery(command: str) -> bool:
    normalized = " ".join(command.split())
    return any(pattern.search(normalized) for pattern in _BROAD_DISCOVERY_PATTERNS)


def _command(payload: dict[str, Any]) -> str:
    value = payload.get("command") or payload.get("cmd")
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return value if isinstance(value, str) else ""


def _output(payload: dict[str, Any]) -> str:
    value = (
        payload.get("aggregated_output")
        or payload.get("output")
        or payload.get("stdout")
        or ""
    )
    return value if isinstance(value, str) else ""


def _tokens(value: str) -> int:
    return (len(value) + 3) // 4
