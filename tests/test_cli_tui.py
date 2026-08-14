from __future__ import annotations

from repo_state_agent.cli import build_parser


def test_run_parser_supports_live_tui_controls() -> None:
    parser = build_parser()
    args = parser.parse_args(["run", ".", "--no-tui"])
    assert args.no_tui
    assert not args.tui

    args = parser.parse_args(["run", ".", "--tui"])
    assert args.tui
    assert not args.no_tui


def test_preview_parser_is_non_agent_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["preview", ".", "--seconds", "2"])
    assert args.command == "preview"
    assert args.seconds == 2.0
