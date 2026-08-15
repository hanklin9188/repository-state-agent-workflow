from __future__ import annotations

from pathlib import Path

from rich.console import Console

from repo_state_agent.runtime.tui.v6 import LiveDashboardV6, should_use_v6_tui


def test_v6_dashboard_tracks_compact_and_efficiency(tmp_path: Path) -> None:
    console = Console(width=110, record=True, force_terminal=False)
    dashboard = LiveDashboardV6(tmp_path, console=console)
    dashboard.handle_supervisor_event({"type": "v6.supervisor.started", "task": "T-1"})
    dashboard.handle_supervisor_event(
        {
            "type": "v6.context.compiled",
            "mode": "CONTINUE",
            "totalTokens": 5800,
            "semanticCapsuleTokens": 1200,
            "repeatedInputTokens": 300,
            "evidenceResendTokens": 0,
        }
    )
    dashboard.handle_supervisor_event(
        {"type": "v6.agent.turn.started", "task": "T-1", "role": "Builder", "mode": "CONTINUE"}
    )
    dashboard.handle_codex_event(
        {
            "type": "turn.completed",
            "usage": {"input_tokens": 40000, "cached_input_tokens": 35000, "output_tokens": 1200},
        }
    )
    dashboard.handle_supervisor_event({"type": "v6.gate", "accepted": True})
    dashboard.handle_supervisor_event(
        {
            "type": "v6.governor",
            "action": "COMPACT",
            "reason": "CONTEXT_OCCUPANCY_PRESSURE",
            "occupancy_ratio": 0.78,
            "occupancy_tokens": 78000,
        }
    )
    console.print(dashboard._render())
    text = console.export_text()
    assert "RSAW 0.7" in text
    assert "LIFECYCLE" in text
    assert "COMPACT" in text
    assert "WORKING MEMORY" in text
    assert "78.0% estimated" in text
    assert "Semantic capsule" in text
    assert "Evidence resend" in text


def test_v6_tui_fallback_rules(monkeypatch) -> None:
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("TERM", "xterm-256color")
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    assert should_use_v6_tui()
    assert not should_use_v6_tui(disable=True)
    assert not should_use_v6_tui(json_output=True)
    assert not should_use_v6_tui(quiet=True)
    assert not should_use_v6_tui(dry_run=True)
