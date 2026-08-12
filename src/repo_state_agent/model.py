from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ActiveState:
    root: Path
    active_path: Path
    task_id: str
    task_spec: Path
    required_reads: tuple[Path, ...]
    next_action: str
    stop_condition: str
    next_role: str
    reasoning: str
