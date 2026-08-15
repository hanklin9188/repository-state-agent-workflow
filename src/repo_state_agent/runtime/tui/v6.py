from __future__ import annotations

import os
import sys
import time
from collections import deque
from pathlib import Path
from threading import RLock
from typing import Any

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ... import __version__
from ...parsing import parse_active


class LiveDashboardV6:
    def __init__(
        self,
        root: Path,
        *,
        console: Console | None = None,
        tool_call_limit: int = 0,
        tool_output_limit: int = 0,
    ) -> None:
        self.root = root.resolve()
        self.console = console or Console(
            no_color=bool(os.environ.get("NO_COLOR")),
            soft_wrap=False,
        )
        self._lock = RLock()
        self._tool_ids: set[str] = set()
        checkpoint = _latest_checkpoint_index(self.root)
        task = "—"
        role = "—"
        status = "STARTING"
        gate = "PENDING"
        try:
            active = parse_active(self.root)
            task = active.task_id or task
            role = active.current_role or active.next_role or role
            if active.human_gate:
                status = "PAUSED"
                gate = "BLOCKED"
        except Exception:
            pass
        self._state: dict[str, Any] = {
            "status": status,
            "task": task,
            "role": role,
            "checkpoint": checkpoint,
            "action": "—",
            "reason": "",
            "envelope": 0,
            "capsule": 0,
            "occupancy": None,
            "input": 0,
            "cached": 0,
            "fresh": 0,
            "model_calls": 0,
            "tool_calls": 0,
            "tool_call_limit": tool_call_limit,
            "tool_output": 0,
            "tool_output_limit": tool_output_limit,
            "repeated": 0,
            "resend": 0,
            "gate": gate,
            "mode": "FRESH",
            "sandbox": "—",
            "sandbox_source": "",
        }
        self._recent: deque[str] = deque(maxlen=6)
        if checkpoint:
            self._recent.appendleft(f"Loaded durable CP-{checkpoint:04d}")
        self._live = Live(
            self._render(),
            console=self.console,
            refresh_per_second=8,
            transient=False,
            redirect_stdout=False,
            redirect_stderr=False,
            vertical_overflow="crop",
        )
        self._active = False

    def __enter__(self) -> "LiveDashboardV6":
        self._live.start(refresh=True)
        self._active = True
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._active:
            self._live.update(self._render(), refresh=True)
            self._live.stop()
            self._active = False

    def handle_supervisor_event(self, event: dict[str, Any]) -> None:
        event_type = str(event.get("type") or "")
        with self._lock:
            if event_type == "v6.supervisor.started":
                self._state.update(
                    status="STARTING",
                    task=event.get("task") or self._state["task"],
                )
                self._push("Supervisor owns checkpoint state")
            elif event_type == "v6.context.compiled":
                self._state["envelope"] = int(event.get("totalTokens") or 0)
                self._state["capsule"] = int(event.get("semanticCapsuleTokens") or 0)
                self._state["repeated"] = int(event.get("repeatedInputTokens") or 0)
                self._state["resend"] = int(event.get("evidenceResendTokens") or 0)
                self._state["mode"] = str(event.get("mode") or "FRESH")
                self._push(f"Context {self._state['mode']} · {self._state['envelope']} tokens")
            elif event_type == "v7.sandbox.resolved":
                self._state["sandbox"] = str(event.get("sandbox") or "—")
                self._state["sandbox_source"] = str(event.get("source") or "")
                self._push(f"Sandbox {self._state['sandbox']} · {self._state['sandbox_source']}")
            elif event_type == "v6.agent.turn.started":
                self._state["status"] = "WORKING"
                self._state["task"] = event.get("task") or self._state["task"]
                self._state["role"] = event.get("role") or self._state["role"]
                self._state["sandbox"] = event.get("sandbox") or self._state["sandbox"]
                self._state["sandbox_source"] = (
                    event.get("sandboxSource") or self._state["sandbox_source"]
                )
                self._state["model_calls"] += 1
                self._push(f"Agent turn · {event.get('mode')}")
            elif event_type == "v6.gate":
                accepted = bool(event.get("accepted"))
                self._state["gate"] = "PASS" if accepted else "REJECT"
                self._state["status"] = "CHECKPOINTING" if accepted else "FAILED"
                self._push("Deterministic gate PASS" if accepted else "Deterministic gate REJECT")
            elif event_type == "v6.governor":
                self._state["action"] = event.get("action") or "—"
                self._state["reason"] = event.get("reason") or ""
                self._state["occupancy"] = event.get("occupancy_ratio")
                if self._state["action"] == "COMPACT":
                    self._state["status"] = "COMPACTING"
                elif self._state["action"] == "ROTATE":
                    self._state["status"] = "ROTATING"
                self._push(f"{self._state['action']} · {self._state['reason']}")
            elif event_type == "v6.checkpoint.sealed":
                checkpoint = str(event.get("checkpoint") or "")
                try:
                    self._state["checkpoint"] = int(checkpoint.split("-")[-1])
                except ValueError:
                    pass
                self._state["status"] = "CHECKPOINTING"
                self._push(f"{checkpoint} sealed")
            elif event_type == "rsaw.tool-budget.exceeded":
                self._state["status"] = "PAUSED"
                self._state["reason"] = str(event.get("violation") or "TOOL_BUDGET")
                self._state["tool_calls"] = int(event.get("tool_calls") or 0)
                self._state["tool_output"] = int(event.get("tool_output_tokens") or 0)
                self._push(f"Tool budget paused · {self._state['reason']}")
            elif event_type == "v6.supervisor.terminal":
                self._state["status"] = event.get("status") or self._state["status"]
                self._state["reason"] = event.get("reason") or self._state["reason"]
                self._push(f"Terminal · {self._state['status']}")
        self._refresh()

    def handle_codex_event(self, event: dict[str, Any]) -> None:
        event_type = str(event.get("type") or "")
        with self._lock:
            if event_type == "turn.completed":
                usage = event.get("usage") if isinstance(event.get("usage"), dict) else {}
                total = int(usage.get("input_tokens") or 0)
                cached = min(total, int(usage.get("cached_input_tokens") or 0))
                self._state["input"] = total
                self._state["cached"] = cached
                self._state["fresh"] = max(0, total - cached)
                self._push(f"Provider input {_fmt(total)} · fresh {_fmt(total - cached)}")
            elif event_type.endswith(".started"):
                item = event.get("item") if isinstance(event.get("item"), dict) else event
                item_type = str(item.get("type") or "")
                if item_type in {
                    "command_execution",
                    "command",
                    "tool_call",
                    "mcp_tool_call",
                    "function_call",
                }:
                    identity = str(item.get("id") or event.get("id") or "")
                    if not identity or identity not in self._tool_ids:
                        if identity:
                            self._tool_ids.add(identity)
                        self._state["tool_calls"] += 1
            elif event_type.endswith(".completed"):
                item = event.get("item") if isinstance(event.get("item"), dict) else event
                output = item.get("aggregated_output") or item.get("output") or item.get("stdout")
                if isinstance(output, str):
                    self._state["tool_output"] += (len(output) + 3) // 4
        self._refresh()

    def finalize(self, status: str, reason: str) -> None:
        with self._lock:
            self._state["status"] = status
            self._state["reason"] = reason
        self._refresh()

    def _push(self, message: str) -> None:
        if not self._recent or self._recent[0] != message:
            self._recent.appendleft(message)

    def _refresh(self) -> None:
        if self._active:
            self._live.update(self._render(), refresh=True)

    def _render(self):
        width = self.console.size.width
        compact = width < 96
        state = dict(self._state)
        status = Text(
            str(state["status"]),
            style=_status_style(str(state["status"])),
        )
        title = Text.assemble(
            (f"RSAW {__version__}", "bold"),
            " · Repository Context Runtime · ",
            status,
        )

        now = Table.grid(expand=True)
        now.add_column(ratio=2)
        now.add_column(ratio=1, justify="right")
        now.add_row(
            f"Task  {state['task']}\n"
            f"Role  {state['role']} · Mode {state['mode']}\n"
            f"Sandbox  {state['sandbox']} · {state['sandbox_source']}",
            f"Durable CP-{int(state['checkpoint']):04d}\nGate {state['gate']}",
        )

        lifecycle = Table.grid(expand=True)
        lifecycle.add_column(ratio=1)
        lifecycle.add_column(ratio=3)
        lifecycle.add_row("NEXT", f"{state['action']}  {state['reason']}")

        occupancy = state.get("occupancy")
        occ = (
            "unknown"
            if not isinstance(occupancy, int | float)
            else f"{float(occupancy) * 100:.1f}% estimated"
        )
        memory = Table.grid(expand=True)
        memory.add_column(ratio=1)
        memory.add_column(ratio=1)
        memory.add_column(ratio=1)
        memory.add_row("Envelope", "Semantic capsule", "Occupancy")
        memory.add_row(
            _fmt(int(state["envelope"])),
            _fmt(int(state["capsule"])),
            occ,
        )

        tool_calls = str(state["tool_calls"])
        if state["tool_call_limit"]:
            tool_calls += f" / {state['tool_call_limit']}"
        tool_output = _fmt(int(state["tool_output"]))
        if state["tool_output_limit"]:
            tool_output += f" / {_fmt(int(state['tool_output_limit']))}"

        efficiency = Table.grid(expand=True)
        efficiency.add_column(ratio=1)
        efficiency.add_column(ratio=1)
        efficiency.add_column(ratio=1)
        efficiency.add_column(ratio=1)
        efficiency.add_row("Input", "Cached", "Fresh", "Model / Tool")
        efficiency.add_row(
            _fmt(int(state["input"])),
            _fmt(int(state["cached"])),
            _fmt(int(state["fresh"])),
            f"{state['model_calls']} / {tool_calls}",
        )
        efficiency.add_row("Tool output", "Repeated", "Evidence resend", "")
        efficiency.add_row(
            tool_output,
            _fmt(int(state["repeated"])),
            _fmt(int(state["resend"])),
            "",
        )

        recent_text = (
            "\n".join(f"• {item}" for item in list(self._recent)[: (3 if compact else 6)])
            or "• Waiting for runtime events"
        )
        footer = (
            "Repository state is authoritative · UI is presentation-only · "
            "expected PAUSE/COMPLETE exits are operator-safe"
        )
        return Panel(
            Group(
                title,
                Panel(now, title="NOW"),
                Panel(lifecycle, title="LIFECYCLE"),
                Panel(memory, title="WORKING MEMORY"),
                Panel(efficiency, title="EFFICIENCY GUARD"),
                Panel(recent_text, title="RECENT"),
                Text(footer, style="dim"),
            ),
            border_style="dim",
        )


def should_use_v6_tui(
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
    if os.environ.get("CI") or os.environ.get("TERM", "").lower() == "dumb":
        return False
    return sys.stdin.isatty() and sys.stdout.isatty()


def preview_v6(root: Path, *, seconds: float = 7.0) -> None:
    dashboard = LiveDashboardV6(
        root,
        tool_call_limit=32,
        tool_output_limit=50_000,
    )
    step = max(0.15, seconds / 9)
    with dashboard:
        dashboard.handle_supervisor_event(
            {
                "type": "v6.supervisor.started",
                "task": "E04-GPU-OBSERVABILITY-DIAGNOSTIC",
                "workstream": "EDGEFLOW_CORE_001",
            }
        )
        time.sleep(step)
        dashboard.handle_supervisor_event(
            {
                "type": "v6.context.compiled",
                "mode": "CONTINUE",
                "totalTokens": 5780,
                "semanticCapsuleTokens": 1310,
                "repeatedInputTokens": 420,
                "evidenceResendTokens": 0,
            }
        )
        dashboard.handle_supervisor_event(
            {
                "type": "v6.agent.turn.started",
                "task": "E04-GPU-OBSERVABILITY-DIAGNOSTIC",
                "role": "Builder",
                "mode": "CONTINUE",
            }
        )
        time.sleep(step)
        dashboard.handle_codex_event(
            {
                "type": "item.started",
                "item": {
                    "id": "tool-1",
                    "type": "command_execution",
                    "command": "pytest tests/test_e04_gpu_observability_diagnostic.py",
                },
            }
        )
        time.sleep(step)
        dashboard.handle_codex_event(
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 38200,
                    "cached_input_tokens": 33100,
                    "output_tokens": 1900,
                },
            }
        )
        dashboard.handle_supervisor_event(
            {"type": "v6.gate", "accepted": True, "errors": [], "warnings": []}
        )
        time.sleep(step)
        dashboard.handle_supervisor_event(
            {
                "type": "v6.governor",
                "action": "COMPACT",
                "reason": "CONTEXT_OCCUPANCY_PRESSURE",
                "occupancy_ratio": 0.78,
                "occupancy_tokens": 99840,
            }
        )
        time.sleep(step * 2)
        dashboard.handle_supervisor_event(
            {
                "type": "v6.checkpoint.sealed",
                "checkpoint": "CP-0007",
                "nextAction": "COMPACT",
            }
        )
        time.sleep(step)
        dashboard.finalize("COMPLETE", "PREVIEW_COMPLETE")
        time.sleep(step)


def _latest_checkpoint_index(root: Path) -> int:
    maximum = 0
    directory = root / ".rsaw/state/checkpoints"
    if not directory.is_dir():
        return 0
    for path in directory.glob("CP-*.json"):
        try:
            maximum = max(maximum, int(path.stem.split("-")[-1]))
        except ValueError:
            continue
    return maximum


def _fmt(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k"
    return str(value)


def _status_style(status: str) -> str:
    return {
        "WORKING": "bold cyan",
        "CHECKPOINTING": "bold green",
        "COMPACTING": "bold yellow",
        "ROTATING": "bold magenta",
        "PAUSED": "bold yellow",
        "COMPLETE": "bold green",
        "FAILED": "bold red",
    }.get(status, "bold")
