from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RuntimeConfig:
    adapter: str = "codex"
    codex_binary: str = "codex"
    model: str | None = None
    profile: str | None = None
    sandbox: str = "workspace-write"
    approve_for_me: bool = False
    max_transitions: int = 100
    max_turns_per_epoch: int = 6
    rotate_input_tokens: int = 60_000
    max_total_input_tokens: int = 5_000_000
    poll_seconds: float = 2.0
    interactive_gates: bool = True
    wait_on_pause: bool = False


def load_runtime_config(root: Path) -> RuntimeConfig:
    path = root.resolve() / ".rsaw/config.json"
    if not path.is_file():
        return RuntimeConfig()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(".rsaw/config.json must contain a JSON object")
    runtime = raw.get("runtime", raw)
    if not isinstance(runtime, dict):
        raise ValueError(".rsaw/config.json runtime must be a JSON object")
    return RuntimeConfig(
        adapter=_str(runtime, "adapter", "codex"),
        codex_binary=_str(runtime, "codex_binary", "codex"),
        model=_optional_str(runtime, "model"),
        profile=_optional_str(runtime, "profile"),
        sandbox=_str(runtime, "sandbox", "workspace-write"),
        approve_for_me=_bool(runtime, "approve_for_me", False),
        max_transitions=_positive_int(runtime, "max_transitions", 100),
        max_turns_per_epoch=_positive_int(runtime, "max_turns_per_epoch", 6),
        rotate_input_tokens=_nonnegative_int(runtime, "rotate_input_tokens", 60_000),
        max_total_input_tokens=_nonnegative_int(
            runtime, "max_total_input_tokens", 5_000_000
        ),
        poll_seconds=_positive_float(runtime, "poll_seconds", 2.0),
        interactive_gates=_bool(runtime, "interactive_gates", True),
        wait_on_pause=_bool(runtime, "wait_on_pause", False),
    )


def _str(data: dict[str, Any], key: str, default: str) -> str:
    value = data.get(key, default)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"runtime.{key} must be a non-empty string")
    return value.strip()


def _optional_str(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValueError(f"runtime.{key} must be a string or null")
    return value.strip()


def _bool(data: dict[str, Any], key: str, default: bool) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"runtime.{key} must be a boolean")
    return value


def _positive_int(data: dict[str, Any], key: str, default: int) -> int:
    value = data.get(key, default)
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"runtime.{key} must be a positive integer")
    return value


def _nonnegative_int(data: dict[str, Any], key: str, default: int) -> int:
    value = data.get(key, default)
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"runtime.{key} must be a non-negative integer")
    return value


def _positive_float(data: dict[str, Any], key: str, default: float) -> float:
    value = data.get(key, default)
    if not isinstance(value, int | float) or value <= 0:
        raise ValueError(f"runtime.{key} must be positive")
    return float(value)
