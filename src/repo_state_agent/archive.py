from __future__ import annotations

import re
from datetime import date
from pathlib import Path


def _slug(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    return normalized or "handoff"


def archive_active(root: Path, label: str, archive_date: date | None = None) -> Path:
    root = root.resolve()
    source = root / "ACTIVE.md"
    if not source.is_file():
        raise FileNotFoundError(source)
    target_dir = root / "docs/handoffs/archive"
    target_dir.mkdir(parents=True, exist_ok=True)
    day = archive_date or date.today()
    target = target_dir / f"{day.isoformat()}_{_slug(label)}.md"
    if target.exists():
        raise FileExistsError(target)
    target.write_bytes(source.read_bytes())
    return target
