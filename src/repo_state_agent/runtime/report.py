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
    input_tokens = _integer(usage.get("input_tokens"))
    cached_tokens = min(input_tokens, _integer(usage.get("cached_input_tokens")))
    fresh_tokens = max(0, input_tokens - cached_tokens)
    output_tokens = _integer(usage.get("output_tokens"))
    checkpoints = _integer(summary.get("checkpoints_observed"))
    turns = _integer(summary.get("agent_turns"))
    transitions = summary.get("transitions", {})
    rotations = _integer(transitions.get("ROTATE")) if isinstance(transitions, dict) else 0
    cache_ratio = round(cached_tokens / input_tokens, 4) if input_tokens else None

    def per_checkpoint(value: int) -> float | None:
        return round(value / checkpoints, 2) if checkpoints else None

    context_efficiency = {
        "fresh_input_tokens": fresh_tokens,
        "cache_reuse_ratio": cache_ratio,
        "input_tokens_per_checkpoint": per_checkpoint(input_tokens),
        "fresh_input_tokens_per_checkpoint": per_checkpoint(fresh_tokens),
        "output_tokens_per_checkpoint": per_checkpoint(output_tokens),
        "turns_per_checkpoint": round(turns / checkpoints, 3) if checkpoints else None,
        "rotations": rotations,
    }
    return {
        "run_id": summary.get("run_id"),
        "status": summary.get("status"),
        "reason": summary.get("reason"),
        "workstream": summary.get("workstream"),
        "agent_turns": turns,
        "runtime_epochs": summary.get("runtime_epochs", 0),
        "fresh_turns": summary.get("fresh_turns", 0),
        "resumed_turns": summary.get("resumed_turns", 0),
        "checkpoints_observed": checkpoints,
        "transitions": transitions,
        "usage": usage,
        "fresh_input_tokens": fresh_tokens,
        "cache_reuse_ratio": cache_ratio,
        "input_tokens_per_checkpoint": context_efficiency["input_tokens_per_checkpoint"],
        "fresh_input_tokens_per_checkpoint": context_efficiency[
            "fresh_input_tokens_per_checkpoint"
        ],
        "context_efficiency": context_efficiency,
        "summary_path": summary.get("summary_path"),
    }


def _integer(value: Any) -> int:
    return int(value) if isinstance(value, int | float) and not isinstance(value, bool) else 0
