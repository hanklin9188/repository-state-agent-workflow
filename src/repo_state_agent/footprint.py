from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from .parsing import parse_active


@dataclass(frozen=True)
class FileFootprint:
    path: Path
    lines: int
    bytes: int
    chars: int
    approx_tokens: int


def measure_file(path: Path) -> FileFootprint:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    return FileFootprint(
        path=path,
        lines=len(text.splitlines()),
        bytes=len(raw),
        chars=len(text),
        approx_tokens=math.ceil(len(text) / 4),
    )


def bootstrap_files(root: Path, include_required: bool = True) -> list[Path]:
    root = root.resolve()
    state = parse_active(root)
    paths = [root / "AGENTS.md", root / "ACTIVE.md", state.task_spec]
    if include_required:
        paths.extend(state.required_reads)

    unique: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen and resolved.is_file():
            unique.append(resolved)
            seen.add(resolved)
    return unique


def measure_bootstrap(root: Path, include_required: bool = True) -> list[FileFootprint]:
    return [measure_file(path) for path in bootstrap_files(root, include_required)]
