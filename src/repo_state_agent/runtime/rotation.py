from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .model import TokenUsage


@dataclass(frozen=True)
class RotationDecision:
    rotate: bool
    reason: str
    input_tokens: int
    cached_input_tokens: int
    fresh_input_tokens: int
    cache_reuse_ratio: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_rotation(
    *,
    usage: TokenUsage,
    thread_turns: int,
    max_turns_per_epoch: int,
    hard_input_tokens: int,
    soft_input_tokens: int,
    max_fresh_input_tokens: int,
    min_cache_reuse_ratio: float,
) -> RotationDecision:
    fresh = max(0, usage.input_tokens - usage.cached_input_tokens)
    ratio = (
        min(1.0, max(0.0, usage.cached_input_tokens / usage.input_tokens))
        if usage.input_tokens > 0
        else None
    )

    def result(rotate: bool, reason: str) -> RotationDecision:
        return RotationDecision(
            rotate=rotate,
            reason=reason,
            input_tokens=usage.input_tokens,
            cached_input_tokens=usage.cached_input_tokens,
            fresh_input_tokens=fresh,
            cache_reuse_ratio=ratio,
        )

    if max_turns_per_epoch and thread_turns >= max_turns_per_epoch:
        return result(True, "MAX_TURNS_PER_RUNTIME_EPOCH")
    if hard_input_tokens and usage.input_tokens >= hard_input_tokens:
        return result(True, "HARD_INPUT_TOKEN_PRESSURE")
    if max_fresh_input_tokens and fresh >= max_fresh_input_tokens:
        return result(True, "FRESH_INPUT_TOKEN_PRESSURE")
    if (
        soft_input_tokens
        and usage.input_tokens >= soft_input_tokens
        and ratio is not None
        and ratio < min_cache_reuse_ratio
    ):
        return result(True, "LOW_CACHE_REUSE_AT_SOFT_LIMIT")
    return result(False, "CACHE_LOCALITY_ACCEPTABLE")
