from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int = 0
    cached_input_tokens: int = 0
    cache_write_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_output_tokens: int = 0

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            cached_input_tokens=self.cached_input_tokens + other.cached_input_tokens,
            cache_write_input_tokens=(
                self.cache_write_input_tokens + other.cache_write_input_tokens
            ),
            output_tokens=self.output_tokens + other.output_tokens,
            reasoning_output_tokens=(self.reasoning_output_tokens + other.reasoning_output_tokens),
        )

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class AgentTurnResult:
    exit_code: int
    thread_id: str | None
    usage: TokenUsage = TokenUsage()
    latest_turn_usage: TokenUsage = TokenUsage()
    last_message: str = ""
    event_count: int = 0
    events_path: Path | None = None
    last_message_path: Path | None = None
    error: str = ""
    interrupted: bool = False

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.error and not self.interrupted


@dataclass(frozen=True)
class AdapterDoctorResult:
    ok: bool
    adapter: str
    binary: str
    version: str = ""
    capabilities: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "adapter": self.adapter,
            "binary": self.binary,
            "version": self.version,
            "capabilities": list(self.capabilities),
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


@dataclass
class RuntimeSummary:
    run_id: str
    repository: str
    adapter: str
    started_at: str
    ended_at: str = ""
    status: str = "RUNNING"
    reason: str = ""
    workstream: str = ""
    initial_task: str = ""
    final_task: str = ""
    runtime_epochs: int = 0
    agent_turns: int = 0
    fresh_turns: int = 0
    resumed_turns: int = 0
    checkpoints_observed: int = 0
    transitions: dict[str, int] = field(default_factory=dict)
    total_usage: TokenUsage = TokenUsage()
    latest_thread_id: str | None = None
    run_dir: str = ""
    last_event_path: str = ""
    last_message_path: str = ""
    human_gate: str = ""
    warnings: list[str] = field(default_factory=list)

    def count_transition(self, action: str) -> None:
        self.transitions[action] = self.transitions.get(action, 0) + 1

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["total_usage"] = self.total_usage.to_dict()
        return payload
