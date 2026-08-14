from __future__ import annotations

import os
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.live import Live

from ...model import ActiveState
from .model import DashboardModel
from .renderer import DashboardRenderable

GateResolver = Callable[[ActiveState], str | None]


class LiveDashboard:
    """In-place terminal dashboard for a running RSAW supervisor."""

    def __init__(
        self,
        root: Path,
        *,
        rotate_input_tokens: int,
        console: Console | None = None,
        refresh_per_second: float = 8.0,
    ) -> None:
        self.root = root.resolve()
        self.model = DashboardModel(self.root, rotate_input_tokens=rotate_input_tokens)
        self.console = console or Console(
            no_color=bool(os.environ.get("NO_COLOR")),
            soft_wrap=False,
        )
        self.renderable = DashboardRenderable(self.model)
        self.live = Live(
            self.renderable,
            console=self.console,
            refresh_per_second=refresh_per_second,
            screen=False,
            transient=False,
            redirect_stdout=False,
            redirect_stderr=False,
            vertical_overflow="crop",
        )
        self._active = False

    def __enter__(self) -> LiveDashboard:
        self.live.start(refresh=True)
        self._active = True
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._active:
            self.live.refresh()
            self.live.stop()
            self._active = False

    def handle_supervisor_event(self, event: dict[str, Any]) -> None:
        self.model.handle_supervisor_event(event)

    def handle_codex_event(self, event: dict[str, Any]) -> None:
        self.model.handle_codex_event(event)

    def finalize(
        self,
        *,
        status: str,
        reason: str,
        summary_path: str = "",
        summary: dict[str, Any] | None = None,
    ) -> None:
        self.model.finalize(
            status=status,
            reason=reason,
            summary_path=summary_path,
            summary=summary,
        )
        if self._active:
            self.live.refresh()

    def settle(self, seconds: float = 0.35) -> None:
        """Allow a final transition frame to become visible without delaying work."""

        if seconds > 0 and self._active:
            time.sleep(seconds)
            self.live.refresh()

    @contextmanager
    def suspended(self) -> Iterator[None]:
        """Temporarily release the terminal for an exact human-gate prompt."""

        was_active = self._active
        if was_active:
            self.live.stop()
            self._active = False
        try:
            yield
        finally:
            if was_active:
                self.live.start(refresh=True)
                self._active = True

    def gate_resolver(self, resolver: GateResolver) -> GateResolver:
        def resolve(state: ActiveState) -> str | None:
            self.model.handle_supervisor_event(
                {
                    "type": "transition",
                    "action": "PAUSE",
                    "reasons": ["HUMAN_GATE"],
                    "task": state.task_id,
                    "epoch": state.epoch_id,
                    "role": state.current_role,
                    "human_gate": state.human_gate or None,
                }
            )
            if self._active:
                self.live.refresh()
                time.sleep(0.1)
            with self.suspended():
                return resolver(state)

        return resolve


def should_use_tui(
    *,
    force: bool = False,
    disable: bool = False,
    json_output: bool = False,
    quiet: bool = False,
    dry_run: bool = False,
) -> bool:
    if disable or json_output or quiet or dry_run:
        return False
    if force:
        return True
    if os.environ.get("TERM", "").lower() == "dumb":
        return False
    if os.environ.get("CI"):
        return False
    return sys.stdin.isatty() and sys.stdout.isatty()


def preview_dashboard(
    root: Path,
    *,
    rotate_input_tokens: int,
    seconds: float = 6.0,
) -> None:
    """Render a deterministic, non-destructive tour of the dashboard states."""

    seconds = max(2.0, seconds)
    step = seconds / 10
    dashboard = LiveDashboard(
        root,
        rotate_input_tokens=rotate_input_tokens,
        refresh_per_second=10,
    )
    with dashboard:
        dashboard.handle_supervisor_event(
            {
                "type": "supervisor_started",
                "run_id": "preview",
                "rotate_input_tokens": rotate_input_tokens,
            }
        )
        time.sleep(step)
        dashboard.handle_supervisor_event(
            {
                "type": "transition",
                "action": "CONTINUE",
                "reasons": ["TIGHTLY_COUPLED_TASK"],
            }
        )
        dashboard.handle_supervisor_event(
            {
                "type": "runtime_epoch_started",
                "runtime_epoch": 3,
                "reason": "preview",
            }
        )
        dashboard.handle_supervisor_event(
            {"type": "agent_turn_started", "turn": 6, "mode": "continue"}
        )
        time.sleep(step)
        dashboard.handle_codex_event(
            {
                "type": "item.started",
                "item": {
                    "type": "command_execution",
                    "command": "pytest tests/runtime/test_gpu_observer.py",
                },
            }
        )
        time.sleep(step * 2)
        dashboard.handle_codex_event(
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": int(rotate_input_tokens * 0.68),
                    "cached_input_tokens": int(rotate_input_tokens * 0.57),
                    "output_tokens": 2100,
                    "reasoning_output_tokens": 800,
                },
            }
        )
        dashboard.handle_supervisor_event({"type": "repository_verification_started"})
        time.sleep(step)
        dashboard.handle_supervisor_event({"type": "repository_verification_passed"})
        dashboard.handle_supervisor_event({"type": "checkpoint_observed", "checkpoint": 6})
        time.sleep(step)
        dashboard.handle_supervisor_event(
            {
                "type": "transition",
                "action": "ROTATE",
                "reasons": ["ROLE_BOUNDARY"],
            }
        )
        time.sleep(step * 2)
        dashboard.handle_supervisor_event(
            {
                "type": "runtime_epoch_started",
                "runtime_epoch": 4,
                "reason": "ROLE_BOUNDARY",
            }
        )
        dashboard.handle_supervisor_event(
            {"type": "agent_turn_started", "turn": 7, "mode": "fresh"}
        )
        time.sleep(step)
        dashboard.finalize(
            status="COMPLETE",
            reason="PREVIEW_COMPLETE",
            summary={
                "runtime_epochs": 4,
                "agent_turns": 7,
                "checkpoints_observed": 7,
                "total_usage": {
                    "input_tokens": 418300,
                    "cached_input_tokens": 337100,
                    "output_tokens": 28400,
                },
            },
        )
        time.sleep(step)
