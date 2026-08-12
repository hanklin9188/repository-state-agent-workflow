from __future__ import annotations

import re
from pathlib import Path

from .model import ActiveState

_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def _sections(text: str) -> dict[str, str]:
    matches = list(_SECTION_RE.finditer(text))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result[match.group(1).strip().lower()] = text[start:end].strip()
    return result


def _field(section: str, name: str) -> str:
    pattern = re.compile(rf"^{re.escape(name)}:\s*(.+?)\s*$", re.MULTILINE | re.IGNORECASE)
    match = pattern.search(section)
    return match.group(1).strip().strip("`") if match else ""


def _bullets(section: str) -> list[str]:
    values: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            value = stripped[2:].strip().strip("`")
            if value and not value.endswith(";"):
                values.append(value)
            elif value:
                values.append(value[:-1])
    return values


def parse_active(root: Path) -> ActiveState:
    active_path = root / "ACTIVE.md"
    text = active_path.read_text(encoding="utf-8")
    sections = _sections(text)

    active_task = sections.get("active task", "")
    task_id = _field(active_task, "ID")
    spec_value = _field(active_task, "Spec")
    task_spec = root / spec_value if spec_value else root / ""

    required = tuple(root / value for value in _bullets(sections.get("required reads", "")))
    next_action = sections.get("next exact action", "").strip()
    stop_condition = sections.get("stop condition", "").strip()
    next_role = sections.get("next session role", "").strip()
    reasoning = sections.get("recommended reasoning", "").strip()

    return ActiveState(
        root=root,
        active_path=active_path,
        task_id=task_id,
        task_spec=task_spec,
        required_reads=required,
        next_action=next_action,
        stop_condition=stop_condition,
        next_role=next_role,
        reasoning=reasoning,
    )
