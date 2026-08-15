from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .active_format import active_budget_errors, canonicalize_active_text
from .continuation import (
    COMPLETE,
    CONTINUE_ALLOWED,
    STOP_REQUIRED,
    VALID_CONTINUATIONS,
)
from .parsing import parse_active

VALID_ROLES = {"builder", "reviewer", "decision", "runner", "analyst"}
VALID_REASONING = {"low", "medium", "high", "extra high", "xhigh", "ultra"}


@dataclass
class VerificationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _role(value: str) -> str:
    return value.strip().lower().replace("_", "-")


def _verify_operator_actions(root: Path, result: VerificationResult) -> None:
    actions = root / ".rsaw/state/operator-actions"
    if not actions.is_dir():
        return
    for path in sorted(actions.glob("*.json")):
        relative = path.relative_to(root).as_posix()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            result.errors.append(f"Operator action is unreadable: {relative}: {exc}")
            continue
        if not isinstance(payload, dict):
            result.errors.append(f"Operator action must be an object: {relative}")
            continue
        schema = str(payload.get("schemaVersion") or "")
        if schema == "rsaw.operator-action.v1":
            result.warnings.append(f"Legacy operator action is not content-bound: {relative}")
            continue
        if schema != "rsaw.operator-action.v2":
            result.errors.append(f"Unsupported operator action schema {schema!r}: {relative}")
            continue
        expected = str(payload.get("contentSha256") or "")
        unsigned = dict(payload)
        unsigned.pop("contentSha256", None)
        canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
        actual = hashlib.sha256(canonical).hexdigest()
        if not expected or expected != actual:
            result.errors.append(f"Operator action checksum mismatch: {relative}")
        for field_name in ("action", "reason", "timestamp"):
            if not str(payload.get(field_name) or "").strip():
                result.errors.append(f"Operator action is missing {field_name}: {relative}")
        operator = payload.get("operator")
        if not isinstance(operator, dict) or not str(operator.get("user") or "").strip():
            result.warnings.append(f"Operator identity is incomplete: {relative}")


def verify_repository(
    root: Path,
    max_lines: int = 140,
    max_bytes: int = 12_288,
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
    canonical = canonicalize_active_text(text)
    result.errors.extend(
        active_budget_errors(
            canonical,
            max_lines=max_lines,
            max_bytes=max_bytes,
        )
    )
    if text != canonical:
        result.warnings.append("ACTIVE.md is not canonical; run `rsaw state normalize .`")

    try:
        state = parse_active(root)
    except Exception as exc:  # pragma: no cover - defensive boundary
        result.errors.append(f"ACTIVE.md could not be parsed: {exc}")
        return result

    if not state.task_id:
        result.errors.append("Active Task ID is missing")
    if not state.task_spec.is_file():
        result.errors.append(f"Active task spec does not exist: {state.task_spec}")

    if state.workstream_id or state.workstream_spec is not None:
        if not state.workstream_id:
            result.errors.append("Workstream ID is missing")
        if state.workstream_spec is None or not state.workstream_spec.is_file():
            result.errors.append(f"Workstream spec does not exist: {state.workstream_spec}")
        if not state.epoch_id:
            result.errors.append("Context Epoch ID is missing")
        if not state.current_role:
            result.errors.append("Context Epoch Role is missing")

    if not state.required_reads:
        result.warnings.append("Required Reads is empty")
    for path in state.required_reads:
        if not path.exists():
            result.errors.append(f"Required read does not exist: {path}")

    if not state.next_action:
        result.errors.append("Next Exact Action is empty")
    if not state.stop_condition:
        result.errors.append("Stop Condition is empty")

    next_role = _role(state.next_role)
    if next_role not in VALID_ROLES:
        result.errors.append(
            f"Next Session Role must be one of {sorted(VALID_ROLES)}; got {state.next_role!r}"
        )

    if state.current_role and _role(state.current_role) not in VALID_ROLES:
        result.errors.append(
            f"Context Epoch Role must be one of {sorted(VALID_ROLES)}; got {state.current_role!r}"
        )

    if state.reasoning.lower() not in VALID_REASONING:
        result.errors.append(
            f"Recommended Reasoning must be one of {sorted(VALID_REASONING)}; "
            f"got {state.reasoning!r}"
        )

    continuation = state.continuation.strip().upper()
    if continuation not in VALID_CONTINUATIONS:
        result.errors.append(
            f"Continuation decision must be one of {sorted(VALID_CONTINUATIONS)}; "
            f"got {state.continuation!r}"
        )

    if state.next_task_id or state.next_task_spec is not None:
        if not state.next_task_id:
            result.errors.append("Next Task ID is missing")
        if state.next_task_spec is None or not state.next_task_spec.is_file():
            result.errors.append(f"Next task spec does not exist: {state.next_task_spec}")

    if continuation == CONTINUE_ALLOWED:
        if state.next_task_spec is None or not state.next_task_spec.is_file():
            result.errors.append("CONTINUE_ALLOWED requires a ready next task spec")
        if state.human_gate:
            result.errors.append("CONTINUE_ALLOWED is incompatible with an active Human Gate")
        if state.current_role and _role(state.current_role) != next_role:
            result.errors.append("CONTINUE_ALLOWED is incompatible with a role change")

    if state.human_gate and continuation != STOP_REQUIRED:
        result.errors.append("An active Human Gate requires STOP_REQUIRED")
    if (
        not state.human_gate
        and continuation == STOP_REQUIRED
        and "human_gate" in state.continuation_reason.lower().replace(" ", "_")
    ):
        result.errors.append("STOP_REQUIRED cites HUMAN_GATE but Human Gate is empty")
    if not state.human_gate and re.search(r"Human Gate active", text, re.IGNORECASE):
        result.warnings.append(
            "ACTIVE.md prose claims Human Gate active while the Human Gate section is empty"
        )

    if continuation == COMPLETE and state.human_gate:
        result.errors.append("COMPLETE is incompatible with an active Human Gate")

    fenced_blocks = re.findall(r"```.*?```", text, flags=re.DOTALL)
    large_blocks = [block for block in fenced_blocks if len(block.splitlines()) > 20]
    if large_blocks:
        result.warnings.append("ACTIVE.md contains a code block longer than 20 lines")

    suspicious = ("Traceback (most recent call last)", "BEGIN RAW LOG", "tool_output")
    for marker in suspicious:
        if marker in text:
            result.warnings.append(f"ACTIVE.md may contain raw log content: {marker}")

    _verify_operator_actions(root, result)
    return result
