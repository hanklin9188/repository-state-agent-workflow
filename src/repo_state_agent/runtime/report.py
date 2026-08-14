from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_runtime_summary(root: Path, run_id: str | None = None) -> dict[str, Any]:
    root = root.resolve()
    runtime_root = root / ".rsaw/runtime"
    if run_id:
        summary_path = runtime_root / run_id / "summary.json"
    else:
        latest_path = runtime_root / "latest.json"
        if not latest_path.is_file():
            raise FileNotFoundError("No RSAW runtime summary exists")
        latest = json.loads(latest_path.read_text(encoding="utf-8"))
        relative = latest.get("summary")
        if not isinstance(relative, str) or not relative:
            raise ValueError(".rsaw/runtime/latest.json is malformed")
        summary_path = root / relative
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Runtime summary is malformed: {summary_path}")
    payload["summary_path"] = str(summary_path.relative_to(root))
    return payload


def efficiency_view(summary: dict[str, Any]) -> dict[str, Any]:
    usage = summary.get("total_usage") if isinstance(summary.get("total_usage"), dict) else {}
    input_tokens = int(usage.get("input_tokens", 0))
    checkpoints = int(summary.get("checkpoints_observed", 0))
    return {
        "run_id": summary.get("run_id"),
        "status": summary.get("status"),
        "reason": summary.get("reason"),
        "workstream": summary.get("workstream"),
        "agent_turns": summary.get("agent_turns", 0),
        "runtime_epochs": summary.get("runtime_epochs", 0),
        "fresh_turns": summary.get("fresh_turns", 0),
        "resumed_turns": summary.get("resumed_turns", 0),
        "checkpoints_observed": checkpoints,
        "transitions": summary.get("transitions", {}),
        "usage": usage,
        "input_tokens_per_checkpoint": (
            round(input_tokens / checkpoints, 2) if checkpoints else None
        ),
        "summary_path": summary.get("summary_path"),
    }
