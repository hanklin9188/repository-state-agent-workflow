"""Live terminal observability for the RSAW runtime supervisor."""

from .live import LiveDashboard, preview_dashboard, should_use_tui
from .model import Activity, DashboardModel, DashboardSnapshot, RecentEvent
from .renderer import DashboardRenderable, build_dashboard, render_dashboard_text

__all__ = [
    "Activity",
    "DashboardModel",
    "DashboardRenderable",
    "DashboardSnapshot",
    "LiveDashboard",
    "RecentEvent",
    "build_dashboard",
    "preview_dashboard",
    "render_dashboard_text",
    "should_use_tui",
]
