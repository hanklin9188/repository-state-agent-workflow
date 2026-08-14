from __future__ import annotations

from pathlib import Path

from repo_state_agent.runtime.codex import CodexAdapter


def test_codex_command_uses_safe_sandbox_and_stdin(tmp_path: Path) -> None:
    adapter = CodexAdapter(binary="codex", sandbox="workspace-write")
    command = adapter.build_command(
        root=tmp_path,
        last_message_path=tmp_path / "last.txt",
        thread_id=None,
    )
    assert "--sandbox" in command
    assert "workspace-write" in command
    assert "--dangerously-bypass-approvals-and-sandbox" not in command
    assert command[-1] == "-"


def test_codex_resume_command_uses_thread_id(tmp_path: Path) -> None:
    adapter = CodexAdapter(binary="codex")
    command = adapter.build_command(
        root=tmp_path,
        last_message_path=tmp_path / "last.txt",
        thread_id="thread-1",
    )
    assert command[-3:] == ["resume", "thread-1", "-"]


def test_automatic_approval_requires_explicit_opt_in(tmp_path: Path) -> None:
    adapter = CodexAdapter(binary="codex", approve_for_me=True)
    command = adapter.build_command(
        root=tmp_path,
        last_message_path=tmp_path / "last.txt",
        thread_id=None,
    )
    assert "--approve-for-me" in command
    assert "--sandbox" not in command
