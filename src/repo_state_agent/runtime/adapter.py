from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .model import AdapterDoctorResult, AgentTurnResult


class AgentAdapter(Protocol):
    name: str

    def doctor(self) -> AdapterDoctorResult: ...

    def run_turn(
        self,
        *,
        prompt: str,
        root: Path,
        run_dir: Path,
        turn_index: int,
        thread_id: str | None,
        environment: dict[str, str],
    ) -> AgentTurnResult: ...
