from __future__ import annotations

from pathlib import Path

from repo_state_agent.prompts import render_prompt
from repo_state_agent.scaffold import initialize_repository


def test_fresh_prompt_orders_stable_before_dynamic_authority(tmp_path: Path) -> None:
    initialize_repository(tmp_path)
    prompt = render_prompt(tmp_path, mode="fresh")
    assert "Resume the active RSAW workstream" in prompt
    assert prompt.index("Stable prefix:") < prompt.index("Dynamic authority:")
    assert prompt.index("AGENTS.md") < prompt.index("ACTIVE.md")
    assert "Stable policy fingerprint:" in prompt
    assert "Estimated bootstrap:" in prompt


def test_continue_prompt_avoids_reloading_stable_prefix(tmp_path: Path) -> None:
    initialize_repository(tmp_path)
    prompt = render_prompt(tmp_path, mode="continue")
    assert "Continue the active RSAW context epoch" in prompt
    assert "Do not reread stable-prefix files" in prompt
    assert "Re-read dynamic authority in this order" in prompt
    assert "docs/tasks/T-000-bootstrap.md" in prompt
