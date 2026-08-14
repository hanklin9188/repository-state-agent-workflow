from __future__ import annotations

import math
from dataclasses import dataclass
from io import StringIO
from time import monotonic

from rich import box
from rich.align import Align
from rich.console import Console, ConsoleOptions, Group, RenderResult
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .model import DashboardModel, DashboardSnapshot, RecentEvent

_STATUS_STYLE = {
    "STARTING": "cyan",
    "WORKING": "cyan",
    "VALIDATING": "bright_cyan",
    "CHECKPOINTING": "green",
    "ROTATING": "yellow",
    "PAUSED": "yellow",
    "FAILED": "red",
    "LIMIT_REACHED": "red",
    "COMPLETE": "green",
    "DRY_RUN": "blue",
}
_STATUS_LABEL = {
    "STARTING": "STARTING",
    "WORKING": "WORKING",
    "VALIDATING": "VALIDATING",
    "CHECKPOINTING": "CHECKPOINT",
    "ROTATING": "ROTATING",
    "PAUSED": "ACTION REQUIRED",
    "FAILED": "FAILED",
    "LIMIT_REACHED": "LIMIT REACHED",
    "COMPLETE": "COMPLETE",
    "DRY_RUN": "DRY RUN",
}
_SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
_PULSE_FRAMES = ("●", "◉", "●", "○")


@dataclass
class _AnimatedPressure:
    value: float = 0.0
    updated_at: float = 0.0

    def step(self, target: float | None, now: float) -> float | None:
        if target is None:
            return None
        if self.updated_at <= 0:
            self.value = target
            self.updated_at = now
            return self.value
        elapsed = max(0.0, now - self.updated_at)
        factor = 1.0 - math.exp(-8.0 * elapsed)
        self.value += (target - self.value) * factor
        self.updated_at = now
        if abs(target - self.value) < 0.002:
            self.value = target
        return self.value


class DashboardRenderable:
    """Live Rich renderable backed by a thread-safe dashboard model."""

    def __init__(self, model: DashboardModel) -> None:
        self.model = model
        self._pressure = _AnimatedPressure()

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        now = monotonic()
        snapshot = self.model.snapshot()
        pressure = self._pressure.step(snapshot.context_pressure, now)
        compact = options.max_width < 96 or console.size.height < 28
        yield build_dashboard(
            snapshot,
            width=options.max_width,
            compact=compact,
            now=now,
            display_pressure=pressure,
        )


def build_dashboard(
    snapshot: DashboardSnapshot,
    *,
    width: int,
    compact: bool,
    now: float | None = None,
    display_pressure: float | None = None,
):
    now = monotonic() if now is None else now
    if _show_transition(snapshot, now):
        return _transition_view(snapshot, width=width, now=now)
    if snapshot.status == "PAUSED":
        return _paused_view(snapshot, width=width, now=now)
    if snapshot.status in {"FAILED", "LIMIT_REACHED"}:
        return _failed_view(snapshot, width=width, now=now)
    if snapshot.status == "COMPLETE":
        return _complete_view(snapshot, width=width, now=now)
    if compact:
        return _compact_view(snapshot, width=width, now=now, pressure=display_pressure)
    return _expanded_view(snapshot, width=width, now=now, pressure=display_pressure)


def render_dashboard_text(
    snapshot: DashboardSnapshot, *, width: int = 100, compact: bool = False
) -> str:
    """Render a deterministic, color-free dashboard string for tests/docs."""

    output = StringIO()
    console = Console(
        file=output,
        width=width,
        color_system=None,
        force_terminal=False,
        legacy_windows=False,
    )
    console.print(
        build_dashboard(
            snapshot,
            width=width,
            compact=compact,
            now=snapshot.started_monotonic + 60,
            display_pressure=snapshot.context_pressure,
        )
    )
    return output.getvalue()


def _expanded_view(
    snapshot: DashboardSnapshot,
    *,
    width: int,
    now: float,
    pressure: float | None,
):
    body = Group(
        _section_now(snapshot, now=now),
        Text(),
        _section_progress(snapshot, width=width),
        Text(),
        _section_context(snapshot, pressure=pressure, width=width),
        Text(),
        _section_recent(snapshot),
        Text(),
        _footer(snapshot, now=now),
    )
    return Panel(
        Padding(body, (0, 1)),
        title=_panel_title(snapshot),
        title_align="left",
        subtitle=_status_text(snapshot, now=now),
        subtitle_align="right",
        border_style=_status_style(snapshot.status),
        box=box.ROUNDED,
        padding=(1, 1),
    )


def _compact_view(
    snapshot: DashboardSnapshot,
    *,
    width: int,
    now: float,
    pressure: float | None,
):
    lines: list[Text] = []
    state_line = Text()
    state_line.append(_animated_symbol(snapshot.status, now), style=_status_style(snapshot.status))
    state_line.append(f" {_STATUS_LABEL.get(snapshot.status, snapshot.status)}", style="bold")
    meta = " · ".join(
        value
        for value in (
            snapshot.role,
            (
                f"Epoch {snapshot.runtime_epoch}"
                if snapshot.runtime_epoch
                else snapshot.declared_epoch
            ),
        )
        if value
    )
    if meta:
        state_line.append(f"  {meta}", style="dim")
    lines.append(state_line)

    activity = Text("NOW  ", style="bold dim")
    activity.append(snapshot.current_activity.title, style="bold")
    if snapshot.current_activity.detail:
        detail = _truncate(snapshot.current_activity.detail, max(30, width - 16))
        activity.append(f"\n     {detail}", style="dim")
    lines.extend([Text(), activity, Text()])

    if snapshot.stages and snapshot.current_stage is not None:
        lines.append(_stage_line(snapshot, max_width=max(30, width - 8)))
        lines.append(Text())

    progress = Text()
    progress.append(f"Checkpoint {snapshot.checkpoints_observed}", style="bold")
    progress.append(" · ")
    progress.append(_human_action(snapshot.next_action), style=_action_style(snapshot.next_action))
    lines.append(progress)

    context = Text("Context ", style="bold dim")
    context.append(_bar(pressure, width=18), style=_pressure_style(pressure))
    context.append(f" {_percent(pressure)}")
    if snapshot.latest_usage.input_tokens:
        context.append(f" · Fresh {_format_tokens(snapshot.fresh_input_tokens)}", style="dim")
    lines.append(context)

    if snapshot.recent_events:
        recent = snapshot.recent_events[0]
        lines.extend([Text(), _recent_line(recent, compact=True)])

    return Panel(
        Padding(Group(*lines), (0, 1)),
        title=_panel_title(snapshot),
        title_align="left",
        subtitle=_footer_compact(snapshot, now=now),
        subtitle_align="right",
        border_style=_status_style(snapshot.status),
        box=box.ROUNDED,
        padding=(0, 1),
    )


def _section_now(snapshot: DashboardSnapshot, *, now: float):
    table = Table.grid(expand=True)
    table.add_column(width=4, no_wrap=True)
    table.add_column(ratio=1)
    spinner = _spinner(now) if snapshot.status in {"STARTING", "WORKING", "VALIDATING"} else "•"
    title = Text(snapshot.current_activity.title, style="bold")
    if snapshot.current_activity.detail:
        title.append(f"\n{_truncate(snapshot.current_activity.detail, 140)}", style="dim")
    table.add_row(Text("NOW", style="bold dim"), Text())
    table.add_row(Text(spinner, style=_status_style(snapshot.status)), title)
    return table


def _section_progress(snapshot: DashboardSnapshot, *, width: int):
    title = Text()
    title.append(snapshot.task_id or "TASK", style="bold cyan")
    if snapshot.task_title:
        title.append(f" · {snapshot.task_title}", style="bold")

    rows = Table.grid(expand=True)
    rows.add_column(width=15, no_wrap=True, style="dim")
    rows.add_column(ratio=1)
    rows.add_row("PROGRESS", title)
    if snapshot.stages and snapshot.current_stage is not None:
        rows.add_row("", _stage_line(snapshot, max_width=max(42, width - 24)))
    rows.add_row("Checkpoint", Text(str(snapshot.checkpoints_observed), style="bold"))
    next_text = Text(_human_action(snapshot.next_action), style=_action_style(snapshot.next_action))
    if snapshot.next_reason:
        next_text.append(f" · {_human_reason(snapshot.next_reason)}", style="dim")
    rows.add_row("Next", next_text)
    if snapshot.next_task_title:
        rows.add_row(
            "Next task",
            Text(
                f"{snapshot.next_task_id} · {snapshot.next_task_title}".strip(" ·"),
                style="dim",
            ),
        )
    return rows


def _section_context(
    snapshot: DashboardSnapshot,
    *,
    pressure: float | None,
    width: int,
):
    heading = Text("CONTEXT PRESSURE", style="bold dim")
    heading.append(f"  {_health_label(pressure)}", style=f"bold {_pressure_style(pressure)}")

    bar_width = max(18, min(42, width - 42))
    bar = Text(_bar(pressure, width=bar_width), style=_pressure_style(pressure))
    bar.append(f"  {_percent(pressure)}", style="bold")

    metrics = Table.grid(expand=True, padding=(0, 2))
    for _ in range(4):
        metrics.add_column(ratio=1)
    metrics.add_row(
        _metric("Input", _format_tokens(snapshot.latest_usage.input_tokens)),
        _metric("Cached", _format_tokens(snapshot.latest_usage.cached_input_tokens)),
        _metric("Fresh", _format_tokens(snapshot.fresh_input_tokens)),
        _metric("Rotate at", _format_tokens(snapshot.rotate_input_tokens)),
    )
    ratio = snapshot.cache_ratio
    if ratio is not None:
        metrics.add_row(
            _metric("Cache reuse", f"{ratio * 100:.0f}%"),
            _metric("Output", _format_tokens(snapshot.latest_usage.output_tokens)),
            _metric("Run input", _format_tokens(snapshot.total_usage.input_tokens)),
            Text(),
        )
    return Group(heading, bar, metrics)


def _section_recent(snapshot: DashboardSnapshot):
    table = Table.grid(expand=True)
    table.add_column(width=8, no_wrap=True)
    table.add_column(ratio=1)
    table.add_row(Text("RECENT", style="bold dim"), Text())
    if not snapshot.recent_events:
        table.add_row(Text("·", style="dim"), Text("Waiting for observable activity", style="dim"))
        return table
    for event in snapshot.recent_events[:3]:
        icon, style = _event_icon(event)
        line = Text(event.title, style=style)
        if event.detail:
            line.append(f" · {_truncate(event.detail, 100)}", style="dim")
        table.add_row(Text(icon, style=style), line)
    return table


def _footer(snapshot: DashboardSnapshot, *, now: float):
    table = Table.grid(expand=True)
    table.add_column(ratio=1)
    table.add_column(ratio=1, justify="center")
    table.add_column(ratio=1, justify="right")
    durable = (
        f"Durable {_ago(snapshot.last_durable_monotonic, now)}"
        if snapshot.last_durable_monotonic is not None
        else "No durable checkpoint yet"
    )
    gate = f"Gate {snapshot.human_gate}" if snapshot.human_gate else "Gate NONE"
    runtime = f"Runtime {_duration(now - snapshot.started_monotonic)}"
    table.add_row(Text(durable, style="dim"), Text(gate, style="dim"), Text(runtime, style="dim"))
    return table


def _transition_view(snapshot: DashboardSnapshot, *, width: int, now: float):
    elapsed = now - (snapshot.transition_started or now)
    dots = "." * (1 + int(elapsed * 4) % 3)
    origin = " · ".join(
        value
        for value in (snapshot.transition_from_role, snapshot.transition_from_epoch)
        if value
    ) or "Current context"
    target = " · ".join(
        value
        for value in (snapshot.transition_to_role or snapshot.role, snapshot.transition_to_epoch)
        if value
    ) or "Fresh context"
    body = Group(
        Align.center(Text("↻", style="bold yellow")),
        Align.center(Text("ROTATING CONTEXT", style="bold yellow")),
        Text(),
        Align.center(Text(origin, style="dim")),
        Align.center(Text("↓", style="yellow")),
        Align.center(Text(target, style="bold")),
        Text(),
        _center_label("Reason", _human_reason(snapshot.transition_reason) or "Context boundary"),
        _center_label("Checkpoint", "Durable ✓"),
        Text(),
        Align.center(Text(f"Starting fresh Codex worker{dots}", style="cyan")),
    )
    return Panel(
        Padding(body, (1, 3)),
        title=f"RSAW · {snapshot.workstream_title or snapshot.project}",
        border_style="yellow",
        box=box.ROUNDED,
        padding=(1, 2),
    )


def _paused_view(snapshot: DashboardSnapshot, *, width: int, now: float):
    gate = snapshot.human_gate or snapshot.reason or "Operator decision required"
    body = Group(
        Align.center(Text("!  ACTION REQUIRED", style="bold yellow")),
        Text(),
        Align.center(Text(snapshot.task_title or snapshot.task_id, style="bold")),
        Align.center(Text(_truncate(gate, max(40, width - 16)), style="yellow")),
        Text(),
        _center_label("Repository", "Durable" if snapshot.last_durable_monotonic else "Verified"),
        _center_label("Worker", "Safely paused"),
        _center_label("Next", "Provide the exact authorized response"),
        Text(),
        Align.center(Text("The supervisor never invents authority.", style="dim")),
    )
    return Panel(
        Padding(body, (1, 3)),
        title=f"RSAW · {snapshot.workstream_title or snapshot.project}",
        border_style="yellow",
        box=box.HEAVY,
        padding=(1, 2),
    )


def _failed_view(snapshot: DashboardSnapshot, *, width: int, now: float):
    body = Group(
        Align.center(Text("✗  SUPERVISOR STOPPED", style="bold red")),
        Text(),
        Align.center(Text(_truncate(snapshot.reason or "Unknown failure", max(40, width - 16)))),
        Text(),
        _center_label("Last task", snapshot.task_title or snapshot.task_id or "—"),
        _center_label(
            "Durable state",
            _ago(snapshot.last_durable_monotonic, now)
            if snapshot.last_durable_monotonic
            else "No new checkpoint",
        ),
        _center_label("Evidence", snapshot.summary_path or "Runtime event log"),
        Text(),
        Align.center(Text("Failure is visible and never silently retried.", style="dim")),
    )
    return Panel(
        Padding(body, (1, 3)),
        title=f"RSAW · {snapshot.workstream_title or snapshot.project}",
        border_style="red",
        box=box.HEAVY,
        padding=(1, 2),
    )


def _complete_view(snapshot: DashboardSnapshot, *, width: int, now: float):
    metrics = Table.grid(expand=False, padding=(0, 3))
    metrics.add_column(justify="right", style="dim")
    metrics.add_column(justify="left", style="bold")
    metrics.add_row("Checkpoints", str(snapshot.checkpoints_observed))
    metrics.add_row("Context epochs", str(snapshot.runtime_epoch))
    metrics.add_row("Agent turns", str(snapshot.agent_turns))
    metrics.add_row("Input", _format_tokens(snapshot.total_usage.input_tokens))
    metrics.add_row("Cached", _format_tokens(snapshot.total_usage.cached_input_tokens))
    metrics.add_row(
        "Fresh",
        _format_tokens(
            max(0, snapshot.total_usage.input_tokens - snapshot.total_usage.cached_input_tokens)
        ),
    )
    metrics.add_row("Runtime", _duration(now - snapshot.started_monotonic))
    body = Group(
        Align.center(Text("✓", style="bold green")),
        Align.center(Text("WORKSTREAM COMPLETE", style="bold green")),
        Text(),
        Align.center(Text(snapshot.workstream_title or snapshot.workstream_id, style="bold")),
        Text(),
        Align.center(metrics),
        Text(),
        Align.center(Text(snapshot.summary_path or "Repository state is durable", style="dim")),
    )
    return Panel(
        Padding(body, (1, 3)),
        title=f"RSAW · {snapshot.workstream_title or snapshot.project}",
        border_style="green",
        box=box.DOUBLE,
        padding=(1, 2),
    )


def _panel_title(snapshot: DashboardSnapshot) -> Text:
    title = Text("RSAW", style="bold")
    title.append(f" · {snapshot.workstream_title or snapshot.project}")
    if snapshot.workstream_id:
        title.append(f"  {snapshot.workstream_id}", style="dim")
    return title


def _status_text(snapshot: DashboardSnapshot, *, now: float) -> Text:
    text = Text()
    text.append(_animated_symbol(snapshot.status, now), style=_status_style(snapshot.status))
    text.append(f" {_STATUS_LABEL.get(snapshot.status, snapshot.status)}", style="bold")
    meta = " · ".join(
        value
        for value in (
            snapshot.role,
            (
                f"Epoch {snapshot.runtime_epoch}"
                if snapshot.runtime_epoch
                else snapshot.declared_epoch
            ),
        )
        if value
    )
    if meta:
        text.append(f"  {meta}", style="dim")
    return text


def _footer_compact(snapshot: DashboardSnapshot, *, now: float) -> Text:
    text = Text()
    if snapshot.last_durable_monotonic is not None:
        text.append(f"Durable {_ago(snapshot.last_durable_monotonic, now)}", style="dim")
    if snapshot.human_gate:
        if text:
            text.append(" · ")
        text.append("Gate ACTIVE", style="yellow")
    return text


def _stage_line(snapshot: DashboardSnapshot, *, max_width: int) -> Text:
    labels = list(snapshot.stages)
    while labels and sum(len(label) + 5 for label in labels) > max_width and len(labels) > 3:
        labels = labels[:2] + ["…"] + labels[-2:]
    line = Text()
    original_index = snapshot.current_stage
    for index, label in enumerate(labels):
        if index:
            line.append("  ─  ", style="dim")
        if label == "…":
            line.append(label, style="dim")
            continue
        stage_index = snapshot.stages.index(label) if label in snapshot.stages else index
        if original_index is not None and stage_index < original_index:
            line.append("✓ ", style="green")
            line.append(label, style="dim")
        elif stage_index == original_index:
            line.append("● ", style="bold cyan")
            line.append(label, style="bold")
        else:
            line.append("○ ", style="dim")
            line.append(label, style="dim")
    return line


def _metric(label: str, value: str) -> Text:
    text = Text()
    text.append(f"{label} ", style="dim")
    text.append(value, style="bold")
    return text


def _recent_line(event: RecentEvent, *, compact: bool) -> Text:
    icon, style = _event_icon(event)
    text = Text(f"{icon} ", style=style)
    text.append(event.title, style=style)
    if event.detail and not compact:
        text.append(f" · {event.detail}", style="dim")
    return text


def _event_icon(event: RecentEvent) -> tuple[str, str]:
    if event.level == "error":
        return "✗", "red"
    if event.level == "success":
        return "✓", "green"
    return {
        "rotate": ("↻", "yellow"),
        "epoch": ("◇", "cyan"),
        "command": ("▶", "cyan"),
        "edit": ("◆", "blue"),
        "read": ("◇", "dim"),
        "tool": ("◈", "cyan"),
        "gate": ("!", "yellow"),
    }.get(event.kind, ("•", "dim"))


def _center_label(label: str, value: str):
    text = Text()
    text.append(f"{label:<12}", style="dim")
    text.append(_truncate(value, 80), style="bold")
    return Align.center(text)


def _animated_symbol(status: str, now: float) -> str:
    if status in {"STARTING", "WORKING", "VALIDATING", "CHECKPOINTING"}:
        return _PULSE_FRAMES[int(now * 2.4) % len(_PULSE_FRAMES)]
    return {
        "ROTATING": "↻",
        "PAUSED": "!",
        "FAILED": "✗",
        "LIMIT_REACHED": "✗",
        "COMPLETE": "✓",
    }.get(status, "•")


def _spinner(now: float) -> str:
    return _SPINNER_FRAMES[int(now * 10) % len(_SPINNER_FRAMES)]


def _show_transition(snapshot: DashboardSnapshot, now: float) -> bool:
    return (
        snapshot.transition_started is not None
        and snapshot.runtime_epoch > 0
        and now - snapshot.transition_started < 1.35
        and snapshot.status not in {"PAUSED", "FAILED", "LIMIT_REACHED", "COMPLETE"}
    )


def _status_style(status: str) -> str:
    return _STATUS_STYLE.get(status, "cyan")


def _action_style(action: str) -> str:
    return {
        "CONTINUE": "green",
        "ROTATE": "yellow",
        "PAUSE": "yellow",
        "COMPLETE": "green",
    }.get(action.upper(), "cyan")


def _human_action(action: str) -> str:
    normalized = action.upper()
    return {
        "CONTINUE": "CONTINUE · same context",
        "ROTATE": "ROTATE · fresh context",
        "PAUSE": "PAUSE · waiting for you",
        "COMPLETE": "COMPLETE",
    }.get(normalized, action or "—")


def _human_reason(reason: str) -> str:
    return reason.replace("_", " ").strip().lower()


def _health_label(pressure: float | None) -> str:
    if pressure is None:
        return "WAITING"
    if pressure < 0.75:
        return "GOOD"
    if pressure < 0.92:
        return "HIGH"
    return "ROTATE SOON"


def _pressure_style(pressure: float | None) -> str:
    if pressure is None:
        return "dim"
    if pressure < 0.75:
        return "green"
    if pressure < 0.92:
        return "yellow"
    return "bold yellow"


def _bar(value: float | None, *, width: int) -> str:
    if value is None:
        return "░" * width
    bounded = min(1.0, max(0.0, value))
    filled = min(width, max(0, round(bounded * width)))
    return "█" * filled + "░" * (width - filled)


def _percent(value: float | None) -> str:
    return "—" if value is None else f"{min(999, round(value * 100))}%"


def _format_tokens(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}m"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k"
    return str(value)


def _duration(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def _ago(timestamp: float | None, now: float) -> str:
    if timestamp is None:
        return "—"
    seconds = max(0, int(now - timestamp))
    if seconds < 2:
        return "now"
    if seconds < 60:
        return f"{seconds}s ago"
    return f"{seconds // 60}m ago"


def _truncate(value: str, limit: int) -> str:
    value = " ".join(value.split())
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "…"
