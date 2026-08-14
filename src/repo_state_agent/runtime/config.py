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
    rotation_soft_input_tokens: int = 48_000
    max_fresh_input_tokens: int = 18_000
    min_cache_reuse_ratio: float = 0.50
    max_total_input_tokens: int = 5_000_000
    poll_seconds: float = 2.0
    interactive_gates: bool = True
    wait_on_pause: bool = False
    bootstrap_token_budget: int = 15_000
    max_context_files: int = 12
    max_context_file_bytes: int = 262_144
    include_workstream_spec: bool = False
    enforce_context_budget: bool = False


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
    rotation = _section(runtime, "rotation")
    context = _section(runtime, "context")

    hard_input = _nested_nonnegative_int(
        rotation,
        "hard_input_tokens",
        runtime,
        "rotate_input_tokens",
        60_000,
    )
    soft_input = _nested_nonnegative_int(
        rotation,
        "soft_input_tokens",
        runtime,
        "rotation_soft_input_tokens",
        48_000,
    )
    soft_is_explicit = "soft_input_tokens" in rotation or "rotation_soft_input_tokens" in runtime
    if hard_input and soft_input > hard_input and not soft_is_explicit:
        soft_input = int(hard_input * 0.8)
    if hard_input and soft_input > hard_input:
        raise ValueError("runtime.rotation.soft_input_tokens cannot exceed hard_input_tokens")

    return RuntimeConfig(
        adapter=_str(runtime, "adapter", "codex"),
        codex_binary=_str(runtime, "codex_binary", "codex"),
        model=_optional_str(runtime, "model"),
        profile=_optional_str(runtime, "profile"),
        sandbox=_str(runtime, "sandbox", "workspace-write"),
        approve_for_me=_bool(runtime, "approve_for_me", False),
        max_transitions=_positive_int(runtime, "max_transitions", 100),
        max_turns_per_epoch=_positive_int(runtime, "max_turns_per_epoch", 6),
        rotate_input_tokens=hard_input,
        rotation_soft_input_tokens=soft_input,
        max_fresh_input_tokens=_nested_nonnegative_int(
            rotation,
            "max_fresh_input_tokens",
            runtime,
            "max_fresh_input_tokens",
            18_000,
        ),
        min_cache_reuse_ratio=_nested_ratio(
            rotation,
            "min_cache_reuse_ratio",
            runtime,
            "min_cache_reuse_ratio",
            0.50,
        ),
        max_total_input_tokens=_nonnegative_int(runtime, "max_total_input_tokens", 5_000_000),
        poll_seconds=_positive_float(runtime, "poll_seconds", 2.0),
        interactive_gates=_bool(runtime, "interactive_gates", True),
        wait_on_pause=_bool(runtime, "wait_on_pause", False),
        bootstrap_token_budget=_nested_positive_int(
            context,
            "bootstrap_token_budget",
            runtime,
            "bootstrap_token_budget",
            15_000,
        ),
        max_context_files=_nested_positive_int(
            context,
            "max_files",
            runtime,
            "max_context_files",
            12,
        ),
        max_context_file_bytes=_nested_positive_int(
            context,
            "max_file_bytes",
            runtime,
            "max_context_file_bytes",
            262_144,
        ),
        include_workstream_spec=_nested_bool(
            context,
            "include_workstream_spec",
            runtime,
            "include_workstream_spec",
            False,
        ),
        enforce_context_budget=_nested_bool(
            context,
            "enforce_budget",
            runtime,
            "enforce_context_budget",
            False,
        ),
    )


def _section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    if not isinstance(value, dict):
        raise ValueError(f"runtime.{key} must be a JSON object")
    return value


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
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"runtime.{key} must be a positive integer")
    return value


def _nonnegative_int(data: dict[str, Any], key: str, default: int) -> int:
    value = data.get(key, default)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"runtime.{key} must be a non-negative integer")
    return value


def _positive_float(data: dict[str, Any], key: str, default: float) -> float:
    value = data.get(key, default)
    if not isinstance(value, int | float) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"runtime.{key} must be positive")
    return float(value)


def _nested_value(
    nested: dict[str, Any],
    nested_key: str,
    parent: dict[str, Any],
    parent_key: str,
    default: Any,
) -> Any:
    if nested_key in nested:
        return nested[nested_key]
    return parent.get(parent_key, default)


def _nested_nonnegative_int(
    nested: dict[str, Any],
    nested_key: str,
    parent: dict[str, Any],
    parent_key: str,
    default: int,
) -> int:
    value = _nested_value(nested, nested_key, parent, parent_key, default)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"runtime.{nested_key} must be a non-negative integer")
    return value


def _nested_positive_int(
    nested: dict[str, Any],
    nested_key: str,
    parent: dict[str, Any],
    parent_key: str,
    default: int,
) -> int:
    value = _nested_value(nested, nested_key, parent, parent_key, default)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"runtime.{nested_key} must be a positive integer")
    return value


def _nested_ratio(
    nested: dict[str, Any],
    nested_key: str,
    parent: dict[str, Any],
    parent_key: str,
    default: float,
) -> float:
    value = _nested_value(nested, nested_key, parent, parent_key, default)
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ValueError(f"runtime.{nested_key} must be a number between 0 and 1")
    result = float(value)
    if result < 0 or result > 1:
        raise ValueError(f"runtime.{nested_key} must be between 0 and 1")
    return result


def _nested_bool(
    nested: dict[str, Any],
    nested_key: str,
    parent: dict[str, Any],
    parent_key: str,
    default: bool,
) -> bool:
    value = _nested_value(nested, nested_key, parent, parent_key, default)
    if not isinstance(value, bool):
        raise ValueError(f"runtime.{nested_key} must be a boolean")
    return value
