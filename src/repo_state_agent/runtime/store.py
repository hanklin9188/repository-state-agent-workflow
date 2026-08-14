from __future__ import annotations

import json
import os
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .model import RuntimeSummary


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


class RuntimeStore:
    def __init__(self, root: Path, run_id: str) -> None:
        self.root = root.resolve()
        self.runtime_root = self.root / ".rsaw/runtime"
        self.run_dir = self.runtime_root / run_id
        self.events_path = self.run_dir / "supervisor-events.jsonl"
        self.summary_path = self.run_dir / "summary.json"
        self.latest_path = self.runtime_root / "latest.json"
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def append_event(self, event: dict[str, Any]) -> None:
        payload = {"timestamp": utc_now(), **event}
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def save_summary(self, summary: RuntimeSummary) -> None:
        payload = summary.to_dict()
        atomic_write_json(self.summary_path, payload)
        atomic_write_json(
            self.latest_path,
            {"run_id": summary.run_id, "summary": str(self.summary_path.relative_to(self.root))},
        )


@dataclass
class RuntimeLock(AbstractContextManager["RuntimeLock"]):
    path: Path
    acquired: bool = False

    @classmethod
    def for_root(cls, root: Path) -> "RuntimeLock":
        return cls(root.resolve() / ".rsaw/runtime.lock")

    def __enter__(self) -> "RuntimeLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"pid": os.getpid(), "created_at": utc_now()}
        try:
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if _stale_lock(self.path):
                self.path.unlink(missing_ok=True)
                descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            else:
                raise RuntimeError(f"Another RSAW supervisor owns {self.path}") from None
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
            handle.write("\n")
        self.acquired = True
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.acquired:
            self.path.unlink(missing_ok=True)
            self.acquired = False


def _stale_lock(path: Path) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        pid = int(payload["pid"])
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    return False
