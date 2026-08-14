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
    workstream_id: str = ""
    workstream_spec: Path | None = None
    epoch_id: str = ""
    current_role: str = ""
    continuation: str = "ROTATE_REQUIRED"
    continuation_reason: str = ""
    next_task_id: str = ""
    next_task_spec: Path | None = None
    human_gate: str = ""
