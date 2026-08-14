from __future__ import annotations

from repo_state_agent.runtime.events import CodexEventAccumulator


def test_codex_json_events_extract_thread_and_usage() -> None:
    accumulator = CodexEventAccumulator()
    accumulator.feed('{"type":"thread.started","thread_id":"abc"}')
    accumulator.feed(
        '{"type":"turn.completed","usage":{"input_tokens":100,'
        '"cached_input_tokens":40,"cache_write_input_tokens":5,'
        '"output_tokens":20,"reasoning_output_tokens":7}}'
    )
    assert accumulator.thread_id == "abc"
    assert accumulator.latest_turn_usage.input_tokens == 100
    assert accumulator.total_usage.cached_input_tokens == 40


def test_non_json_diagnostics_do_not_break_event_parser() -> None:
    accumulator = CodexEventAccumulator()
    assert accumulator.feed("warning: diagnostic") is None
    assert accumulator.event_count == 0
