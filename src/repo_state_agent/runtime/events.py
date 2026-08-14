from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .model import TokenUsage


@dataclass
class CodexEventAccumulator:
    thread_id: str | None = None
    total_usage: TokenUsage = TokenUsage()
    latest_turn_usage: TokenUsage = TokenUsage()
    event_count: int = 0
    turn_completed: bool = False
    errors: list[str] = field(default_factory=list)

    def feed(self, line: str) -> dict[str, Any] | None:
        stripped = line.strip()
        if not stripped:
            return None
        try:
            event = json.loads(stripped)
        except json.JSONDecodeError:
            return None
        if not isinstance(event, dict):
            return None

        self.event_count += 1
        event_type = event.get("type")
        if event_type == "thread.started":
            thread_id = event.get("thread_id")
            if isinstance(thread_id, str) and thread_id:
                self.thread_id = thread_id
        elif event_type == "turn.completed":
            usage = _usage(event.get("usage"))
            self.latest_turn_usage = usage
            self.total_usage = self.total_usage + usage
            self.turn_completed = True
        elif event_type == "turn.failed":
            message = _error_message(event.get("error"))
            if message:
                self.errors.append(message)
        elif event_type == "error":
            message = _error_message(event)
            if message:
                self.errors.append(message)
        return event


def _int(value: Any) -> int:
    return int(value) if isinstance(value, int | float) else 0


def _usage(value: Any) -> TokenUsage:
    if not isinstance(value, dict):
        return TokenUsage()
    return TokenUsage(
        input_tokens=_int(value.get("input_tokens")),
        cached_input_tokens=_int(value.get("cached_input_tokens")),
        cache_write_input_tokens=_int(value.get("cache_write_input_tokens")),
        output_tokens=_int(value.get("output_tokens")),
        reasoning_output_tokens=_int(value.get("reasoning_output_tokens")),
    )


def _error_message(value: Any) -> str:
    if isinstance(value, dict):
        message = value.get("message")
        return message if isinstance(message, str) else ""
    return value if isinstance(value, str) else ""
