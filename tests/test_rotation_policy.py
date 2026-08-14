from __future__ import annotations

from repo_state_agent.runtime.model import TokenUsage
from repo_state_agent.runtime.rotation import evaluate_rotation


def decide(input_tokens: int, cached: int, turns: int = 1):
    return evaluate_rotation(
        usage=TokenUsage(input_tokens=input_tokens, cached_input_tokens=cached),
        thread_turns=turns,
        max_turns_per_epoch=6,
        hard_input_tokens=60_000,
        soft_input_tokens=48_000,
        max_fresh_input_tokens=18_000,
        min_cache_reuse_ratio=0.5,
    )


def test_hard_and_turn_limits_rotate() -> None:
    assert decide(10_000, 8_000, turns=6).reason == "MAX_TURNS_PER_RUNTIME_EPOCH"
    assert decide(60_000, 55_000).reason == "HARD_INPUT_TOKEN_PRESSURE"


def test_fresh_input_pressure_rotates() -> None:
    decision = decide(40_000, 20_000)
    assert decision.rotate
    assert decision.reason == "FRESH_INPUT_TOKEN_PRESSURE"
    assert decision.fresh_input_tokens == 20_000


def test_soft_limit_uses_cache_quality() -> None:
    bad = decide(50_000, 20_000)
    good = decide(50_000, 40_000)
    assert bad.rotate and bad.reason == "FRESH_INPUT_TOKEN_PRESSURE"
    assert not good.rotate
    assert good.reason == "CACHE_LOCALITY_ACCEPTABLE"


def test_low_cache_reason_when_fresh_limit_is_disabled() -> None:
    decision = evaluate_rotation(
        usage=TokenUsage(input_tokens=50_000, cached_input_tokens=20_000),
        thread_turns=1,
        max_turns_per_epoch=6,
        hard_input_tokens=60_000,
        soft_input_tokens=48_000,
        max_fresh_input_tokens=0,
        min_cache_reuse_ratio=0.5,
    )
    assert decision.rotate
    assert decision.reason == "LOW_CACHE_REUSE_AT_SOFT_LIMIT"
