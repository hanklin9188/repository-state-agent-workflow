from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .parsing import parse_active


@dataclass
class VerificationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def verify_repository(
    root: Path, max_lines: int = 120, max_bytes: int = 10_240
) -> VerificationResult:
    root = root.resolve()
    result = VerificationResult()
    active_path = root / "ACTIVE.md"
    agents_path = root / "AGENTS.md"

    if not agents_path.is_file():
        result.errors.append("AGENTS.md is missing")
    if not active_path.is_file():
        result.errors.append("ACTIVE.md is missing")
        return result

    raw = active_path.read_bytes()
    text = raw.decode("utf-8")
    line_count = len(text.splitlines())
    if line_count > max_lines:
        result.errors.append(f"ACTIVE.md has {line_count} lines; limit is {max_lines}")
    if len(raw) > max_bytes:
        result.errors.append(f"ACTIVE.md has {len(raw)} bytes; limit is {max_bytes}")

    try:
        state = parse_active(root)
    except Exception as exc:  # pragma: no cover - defensive boundary
        result.errors.append(f"ACTIVE.md could not be parsed: {exc}")
        return result

    if not state.task_id:
        result.errors.append("Active Task ID is missing")
    if not state.task_spec.is_file():
        result.errors.append(f"Active task spec does not exist: {state.task_spec}")

    if not state.required_reads:
        result.warnings.append("Required Reads is empty")
    for path in state.required_reads:
        if not path.exists():
            result.errors.append(f"Required read does not exist: {path}")

    if not state.next_action:
        result.errors.append("Next Exact Action is empty")
    if not state.stop_condition:
        result.errors.append("Stop Condition is empty")

    valid_roles = {"builder", "reviewer", "decision"}
    if state.next_role.lower() not in valid_roles:
        result.errors.append(
            f"Next Session Role must be one of {sorted(valid_roles)}; got {state.next_role!r}"
        )

    valid_reasoning = {"low", "medium", "high", "extra high", "xhigh"}
    if state.reasoning.lower() not in valid_reasoning:
        result.errors.append(
            f"Recommended Reasoning must be one of {sorted(valid_reasoning)}; "
            f"got {state.reasoning!r}"
        )

    fenced_blocks = re.findall(r"```.*?```", text, flags=re.DOTALL)
    large_blocks = [block for block in fenced_blocks if len(block.splitlines()) > 20]
    if large_blocks:
        result.warnings.append("ACTIVE.md contains a code block longer than 20 lines")

    suspicious = ("Traceback (most recent call last)", "BEGIN RAW LOG", "tool_output")
    for marker in suspicious:
        if marker in text:
            result.warnings.append(f"ACTIVE.md may contain raw log content: {marker}")

    return result
