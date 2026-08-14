from __future__ import annotations

import re
from pathlib import Path

from .model import ActiveState

_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_NONE_VALUES = {"", "none", "none.", "no", "n/a", "not applicable"}


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


def _path(root: Path, value: str) -> Path | None:
    return (root / value).resolve() if value else None


def _normalized_gate(value: str) -> str:
    return "" if value.strip().lower() in _NONE_VALUES else value.strip()


def parse_active(root: Path) -> ActiveState:
    root = root.resolve()
    active_path = root / "ACTIVE.md"
    text = active_path.read_text(encoding="utf-8")
    sections = _sections(text)

    active_task = sections.get("active task", "")
    task_id = _field(active_task, "ID")
    spec_value = _field(active_task, "Spec")
    task_spec = _path(root, spec_value) or root / "__missing_active_task__"

    workstream = sections.get("workstream", "")
    workstream_id = _field(workstream, "ID")
    workstream_spec = _path(root, _field(workstream, "Spec"))

    epoch = sections.get("context epoch", "")
    epoch_id = _field(epoch, "ID")
    current_role = _field(epoch, "Role")

    continuation_section = sections.get("continuation gate", "")
    continuation = _field(continuation_section, "Decision") or "ROTATE_REQUIRED"
    continuation_reason = _field(continuation_section, "Reason")

    next_task = sections.get("next task", "")
    next_task_id = _field(next_task, "ID")
    next_task_spec = _path(root, _field(next_task, "Spec"))

    required = tuple(root / value for value in _bullets(sections.get("required reads", "")))
    next_action = sections.get("next exact action", "").strip()
    stop_condition = sections.get("stop condition", "").strip()
    next_role = sections.get("next session role", "").strip()
    reasoning = sections.get("recommended reasoning", "").strip()
    human_gate = _normalized_gate(sections.get("human gate", ""))

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
        workstream_id=workstream_id,
        workstream_spec=workstream_spec,
        epoch_id=epoch_id,
        current_role=current_role,
        continuation=continuation,
        continuation_reason=continuation_reason,
        next_task_id=next_task_id,
        next_task_spec=next_task_spec,
        human_gate=human_gate,
    )
