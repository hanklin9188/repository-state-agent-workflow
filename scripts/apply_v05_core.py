from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(relative: str, content: str) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


write(
    "src/repo_state_agent/__init__.py",
    '''"""Repository-State Agent Workflow utilities."""

__version__ = "0.5.0"
''',
)

write(
    "pyproject.toml",
    '''[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[project]
name = "repository-state-agent-workflow"
version = "0.5.0"
description = "Repository-backed workstreams with cache-aware context planning and live runtime observability"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [{ name = "Hank" }]
dependencies = [
  "rich>=14.2,<16",
]
keywords = [
  "coding-agents",
  "ai-agents",
  "agent-workflow",
  "repository-state",
  "context-engineering",
  "context-planning",
  "cache-efficiency",
  "persistent-workstreams",
  "context-rotation",
  "runtime-supervisor",
  "terminal-ui",
  "agent-observability",
  "progressive-disclosure",
  "developer-tools",
  "software-engineering",
]
classifiers = [
  "Development Status :: 3 - Alpha",
  "License :: OSI Approved :: MIT License",
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3.10",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
  "Programming Language :: Python :: 3.13",
  "Topic :: Software Development :: Quality Assurance",
  "Topic :: Software Development :: Libraries :: Python Modules",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "ruff>=0.9",
]

[project.scripts]
rsaw = "repo_state_agent.cli:main"

[project.urls]
Homepage = "https://github.com/hanklin9188/repository-state-agent-workflow"
Documentation = "https://github.com/hanklin9188/repository-state-agent-workflow#documentation"
Repository = "https://github.com/hanklin9188/repository-state-agent-workflow"
Issues = "https://github.com/hanklin9188/repository-state-agent-workflow/issues"
Changelog = "https://github.com/hanklin9188/repository-state-agent-workflow/blob/main/CHANGELOG.md"

[tool.setuptools]
package-dir = {"" = "src" }
include-package-data = true

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
repo_state_agent = ["templates/*.md", "templates/*.json", "templates/*.txt"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.ruff.lint.per-file-ignores]
"src/repo_state_agent/runtime/supervisor.py" = ["UP035"]
"tests/test_codex_adapter_subprocess.py" = ["I001"]
"tests/test_codex_adapter_lifecycle.py" = ["I001"]
''',
)

write(
    "src/repo_state_agent/runtime/config.py",
    '''from __future__ import annotations

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
        max_total_input_tokens=_nonnegative_int(
            runtime, "max_total_input_tokens", 5_000_000
        ),
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
''',
)

write(
    "src/repo_state_agent/runtime/context.py",
    '''from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ..model import ActiveState
from ..parsing import parse_active


@dataclass(frozen=True)
class ContextDocument:
    path: str
    category: str
    bytes: int
    chars: int
    approx_tokens: int
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ContextPlan:
    documents: tuple[ContextDocument, ...]
    budget_tokens: int
    max_files: int
    stable_fingerprint: str
    dynamic_fingerprint: str
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def total_tokens(self) -> int:
        return sum(document.approx_tokens for document in self.documents)

    @property
    def stable_tokens(self) -> int:
        return sum(
            document.approx_tokens
            for document in self.documents
            if document.category == "stable"
        )

    @property
    def dynamic_tokens(self) -> int:
        return self.total_tokens - self.stable_tokens

    @property
    def within_budget(self) -> bool:
        return self.total_tokens <= self.budget_tokens

    @property
    def ok(self) -> bool:
        return not self.errors and self.within_budget

    def to_dict(self) -> dict[str, Any]:
        return {
            "documents": [document.to_dict() for document in self.documents],
            "document_count": len(self.documents),
            "total_tokens": self.total_tokens,
            "stable_tokens": self.stable_tokens,
            "dynamic_tokens": self.dynamic_tokens,
            "budget_tokens": self.budget_tokens,
            "within_budget": self.within_budget,
            "stable_fingerprint": self.stable_fingerprint,
            "dynamic_fingerprint": self.dynamic_fingerprint,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def build_context_plan(
    root: Path,
    *,
    budget_tokens: int = 15_000,
    max_files: int = 12,
    max_file_bytes: int = 262_144,
    include_workstream_spec: bool = False,
    state: ActiveState | None = None,
) -> ContextPlan:
    root = root.resolve()
    state = state or parse_active(root)
    candidates: list[tuple[Path, str]] = [(root / "AGENTS.md", "stable")]
    if include_workstream_spec and state.workstream_spec is not None:
        candidates.append((state.workstream_spec, "stable"))
    candidates.extend(
        [
            (root / "ACTIVE.md", "active"),
            (state.task_spec, "task"),
        ]
    )
    candidates.extend((path, "required") for path in state.required_reads)

    documents: list[ContextDocument] = []
    errors: list[str] = []
    warnings: list[str] = []
    seen: set[Path] = set()
    for candidate, category in candidates:
        path = candidate.resolve()
        if path in seen:
            continue
        seen.add(path)
        try:
            relative = path.relative_to(root)
        except ValueError:
            errors.append(f"Context path escapes repository: {path}")
            continue
        if not path.is_file():
            errors.append(f"Context file does not exist: {relative.as_posix()}")
            continue
        size = path.stat().st_size
        if size > max_file_bytes:
            errors.append(
                f"Context file exceeds {max_file_bytes} bytes: {relative.as_posix()} ({size})"
            )
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"Context file is not UTF-8 text: {relative.as_posix()}")
            continue
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        documents.append(
            ContextDocument(
                path=relative.as_posix(),
                category=category,
                bytes=size,
                chars=len(text),
                approx_tokens=(len(text) + 3) // 4,
                sha256=digest,
            )
        )

    if len(documents) > max_files:
        errors.append(f"Context plan has {len(documents)} files; configured maximum is {max_files}")

    total_tokens = sum(document.approx_tokens for document in documents)
    if total_tokens > budget_tokens:
        warnings.append(
            f"Context plan is approximately {total_tokens} tokens; budget is {budget_tokens}"
        )

    stable = tuple(document for document in documents if document.category == "stable")
    dynamic = tuple(document for document in documents if document.category != "stable")
    return ContextPlan(
        documents=tuple(documents),
        budget_tokens=budget_tokens,
        max_files=max_files,
        stable_fingerprint=_fingerprint(stable),
        dynamic_fingerprint=_fingerprint(dynamic),
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _fingerprint(documents: tuple[ContextDocument, ...]) -> str:
    payload = "\n".join(
        f"{document.category}:{document.path}:{document.sha256}" for document in documents
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
''',
)

write(
    "src/repo_state_agent/runtime/rotation.py",
    '''from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .model import TokenUsage


@dataclass(frozen=True)
class RotationDecision:
    rotate: bool
    reason: str
    input_tokens: int
    cached_input_tokens: int
    fresh_input_tokens: int
    cache_reuse_ratio: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_rotation(
    *,
    usage: TokenUsage,
    thread_turns: int,
    max_turns_per_epoch: int,
    hard_input_tokens: int,
    soft_input_tokens: int,
    max_fresh_input_tokens: int,
    min_cache_reuse_ratio: float,
) -> RotationDecision:
    fresh = max(0, usage.input_tokens - usage.cached_input_tokens)
    ratio = (
        min(1.0, max(0.0, usage.cached_input_tokens / usage.input_tokens))
        if usage.input_tokens > 0
        else None
    )

    def result(rotate: bool, reason: str) -> RotationDecision:
        return RotationDecision(
            rotate=rotate,
            reason=reason,
            input_tokens=usage.input_tokens,
            cached_input_tokens=usage.cached_input_tokens,
            fresh_input_tokens=fresh,
            cache_reuse_ratio=ratio,
        )

    if max_turns_per_epoch and thread_turns >= max_turns_per_epoch:
        return result(True, "MAX_TURNS_PER_RUNTIME_EPOCH")
    if hard_input_tokens and usage.input_tokens >= hard_input_tokens:
        return result(True, "HARD_INPUT_TOKEN_PRESSURE")
    if max_fresh_input_tokens and fresh >= max_fresh_input_tokens:
        return result(True, "FRESH_INPUT_TOKEN_PRESSURE")
    if (
        soft_input_tokens
        and usage.input_tokens >= soft_input_tokens
        and ratio is not None
        and ratio < min_cache_reuse_ratio
    ):
        return result(True, "LOW_CACHE_REUSE_AT_SOFT_LIMIT")
    return result(False, "CACHE_LOCALITY_ACCEPTABLE")
''',
)

write(
    "src/repo_state_agent/runtime/report.py",
    '''from __future__ import annotations

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
''',
)

write(
    "src/repo_state_agent/prompts.py",
    '''from __future__ import annotations

from pathlib import Path

from .continuation import decide_continuation
from .parsing import parse_active
from .runtime.config import RuntimeConfig, load_runtime_config
from .runtime.context import ContextPlan, build_context_plan

VALID_ROLES = {"builder", "reviewer", "decision", "runner", "analyst"}
VALID_MODES = {"auto", "fresh", "continue"}

ROLE_INSTRUCTIONS = {
    "builder": """Execute the active task through its stop condition.
Use V0/V1 checks while iterating and one V2 closure check when the context epoch closes.
At every task checkpoint, persist evidence and update ACTIVE.md.
""",
    "reviewer": """Act as a fresh reviewer.
Read the governing spec, diff or commit, tests, and evidence.
Do not preload the builder's debugging history.
Report correctness, spec compliance, regression risk, and blocking findings.
Update ACTIVE.md at the review boundary.
""",
    "decision": """Use the two-pass Medium decision workflow.
Pass A decomposes facts, inferences, options, constraints, and missing evidence.
Pass B synthesizes the decision and records assumptions.
Do not implement the decision in this context epoch.
Update ACTIVE.md at the decision boundary.
""",
    "runner": """Execute only the registered or authorized run described by the active task.
Preserve raw evidence and do not redesign after observing results.
Update ACTIVE.md at the execution boundary.
""",
    "analyst": """Analyze only the sealed evidence and governing protocol referenced by
the active task.
Do not reuse the runner's exploratory context or modify raw evidence.
Record the scoped conclusion, next scientific action, and update ACTIVE.md.
""",
}


def _role_for(state_role: str, next_role: str, requested: str | None) -> str:
    role = (requested or state_role or next_role or "builder").strip().lower().replace("_", "-")
    if role not in VALID_ROLES:
        raise ValueError(f"Unknown role: {role}")
    return role


def render_prompt(
    root: Path,
    role: str | None = None,
    mode: str = "auto",
    *,
    config: RuntimeConfig | None = None,
) -> str:
    root = root.resolve()
    state = parse_active(root)
    config = config or load_runtime_config(root)
    selected_role = _role_for(state.current_role, state.next_role, role)
    normalized_mode = mode.strip().lower()
    if normalized_mode not in VALID_MODES:
        raise ValueError(f"Unknown mode: {mode}")

    decision = decide_continuation(state)
    if normalized_mode == "fresh":
        opening = "Resume the active RSAW workstream from repository state."
        resolved_mode = "fresh"
    elif normalized_mode == "continue":
        opening = "Continue the active RSAW context epoch from repository state."
        resolved_mode = "continue"
    else:
        resolved_mode = "continue" if decision.may_continue else "fresh"
        opening = (
            "Continue the active RSAW context epoch from repository state."
            if resolved_mode == "continue"
            else "Resume the active RSAW workstream from repository state."
        )

    plan = build_context_plan(
        root,
        budget_tokens=config.bootstrap_token_budget,
        max_files=config.max_context_files,
        max_file_bytes=config.max_context_file_bytes,
        include_workstream_spec=config.include_workstream_spec,
        state=state,
    )
    reads = _render_reads(plan, resolved_mode)
    task = state.task_spec.relative_to(root).as_posix()
    workstream = (
        state.workstream_spec.relative_to(root).as_posix()
        if state.workstream_spec and state.workstream_spec.is_relative_to(root)
        else "not configured"
    )

    return f"""Work in this repository.

RSAW EXECUTION CONTRACT

Repository state is authoritative over conversation history. Keep the workstream
durable and the model context bounded. Use progressive disclosure: read only the
ordered context plan, then expand only when the active task requires evidence.

{opening}

{reads}

Workstream: {state.workstream_id or 'classic'} ({workstream})
Context epoch: {state.epoch_id or 'fresh-task'}
Role: {selected_role}
Active task: {state.task_id} ({task})
Stable policy fingerprint: {plan.stable_fingerprint[:16]}
Dynamic authority fingerprint: {plan.dynamic_fingerprint[:16]}
Estimated bootstrap: {plan.total_tokens} / {plan.budget_tokens} tokens

{ROLE_INSTRUCTIONS[selected_role]}
When the active task reaches a checkpoint:
- persist evidence and commit or record the durable state;
- activate the next task in ACTIVE.md;
- run `rsaw verify .` and, in manual mode, run `rsaw next .`;
- declare CONTINUE_ALLOWED, ROTATE_REQUIRED, STOP_REQUIRED, or COMPLETE;
- do not weaken safety, validation, or scientific role boundaries to save context.
"""


def _render_reads(plan: ContextPlan, mode: str) -> str:
    stable = [document.path for document in plan.documents if document.category == "stable"]
    dynamic = [document.path for document in plan.documents if document.category != "stable"]
    if mode == "continue":
        lines = [
            "Reuse the current bounded context. Do not reread stable-prefix files unless",
            "their fingerprint changed or the active task explicitly requires them.",
            "",
            "Re-read dynamic authority in this order:",
        ]
        lines.extend(f"{index}. {path}" for index, path in enumerate(dynamic, 1))
        lines.extend(
            [
                "",
                "Stable prefix already available in this thread:",
                *(f"- {path}" for path in stable),
            ]
        )
        return "\n".join(lines)

    lines = ["Read only this ordered bootstrap context:", "", "Stable prefix:"]
    lines.extend(f"{index}. {path}" for index, path in enumerate(stable, 1))
    lines.append("")
    lines.append("Dynamic authority:")
    lines.extend(f"{index}. {path}" for index, path in enumerate(dynamic, 1))
    return "\n".join(lines)
''',
)

write(
    "src/repo_state_agent/runtime/supervisor.py",
    '''from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from ..continuation import (
    ACTION_COMPLETE,
    ACTION_PAUSE,
    ACTION_ROTATE,
    decide_continuation,
)
from ..model import ActiveState
from ..parsing import parse_active
from ..prompts import render_prompt
from ..verify import verify_repository
from .adapter import AgentAdapter
from .config import RuntimeConfig
from .context import ContextPlan, build_context_plan
from .model import RuntimeSummary
from .rotation import evaluate_rotation
from .store import RuntimeLock, RuntimeLockError, RuntimeStore, utc_now

STATUS_COMPLETE = "COMPLETE"
STATUS_PAUSED = "PAUSED"
STATUS_FAILED = "FAILED"
STATUS_LIMIT_REACHED = "LIMIT_REACHED"
STATUS_DRY_RUN = "DRY_RUN"


@dataclass(frozen=True)
class SupervisorOptions:
    dry_run: bool = False
    wait_on_pause: bool = False
    poll_seconds: float = 2.0
    max_transitions: int = 100
    max_turns_per_epoch: int = 6
    rotate_input_tokens: int = 60_000
    rotation_soft_input_tokens: int = 48_000
    max_fresh_input_tokens: int = 18_000
    min_cache_reuse_ratio: float = 0.50
    max_total_input_tokens: int = 5_000_000
    bootstrap_token_budget: int = 15_000
    max_context_files: int = 12
    max_context_file_bytes: int = 262_144
    include_workstream_spec: bool = False
    enforce_context_budget: bool = False
    quiet: bool = False


@dataclass(frozen=True)
class SupervisorResult:
    status: str
    reason: str
    summary_path: Path | None
    run_id: str
    exit_code: int


GateResolver = Callable[[ActiveState], str | None]
RuntimeEventSink = Callable[[dict[str, Any]], None]


def options_from_config(
    config: RuntimeConfig, *, dry_run: bool = False, quiet: bool = False
) -> SupervisorOptions:
    return SupervisorOptions(
        dry_run=dry_run,
        wait_on_pause=config.wait_on_pause,
        poll_seconds=config.poll_seconds,
        max_transitions=config.max_transitions,
        max_turns_per_epoch=config.max_turns_per_epoch,
        rotate_input_tokens=config.rotate_input_tokens,
        rotation_soft_input_tokens=config.rotation_soft_input_tokens,
        max_fresh_input_tokens=config.max_fresh_input_tokens,
        min_cache_reuse_ratio=config.min_cache_reuse_ratio,
        max_total_input_tokens=config.max_total_input_tokens,
        bootstrap_token_budget=config.bootstrap_token_budget,
        max_context_files=config.max_context_files,
        max_context_file_bytes=config.max_context_file_bytes,
        include_workstream_spec=config.include_workstream_spec,
        enforce_context_budget=config.enforce_context_budget,
        quiet=quiet,
    )


def supervise(
    root: Path,
    adapter: AgentAdapter,
    options: SupervisorOptions,
    *,
    gate_resolver: GateResolver | None = None,
    event_sink: RuntimeEventSink | None = None,
) -> SupervisorResult:
    root = root.resolve()
    initial_verification = verify_repository(root)
    if not initial_verification.ok:
        _notify_event(
            event_sink,
            {"type": "repository_verification_failed", "errors": list(initial_verification.errors)},
        )
        return SupervisorResult(
            status=STATUS_FAILED,
            reason="REPOSITORY_VERIFICATION_FAILED: " + "; ".join(initial_verification.errors),
            summary_path=None,
            run_id="",
            exit_code=23,
        )

    initial_state = parse_active(root)
    run_id = f"rsaw-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    store = RuntimeStore(root, run_id)
    summary = RuntimeSummary(
        run_id=run_id,
        repository=str(root),
        adapter=adapter.name,
        started_at=utc_now(),
        workstream=initial_state.workstream_id,
        initial_task=initial_state.task_id,
        run_dir=str(store.run_dir.relative_to(root)),
    )
    store.save_summary(summary)
    _record_event(
        store,
        event_sink,
        {
            "type": "supervisor_started",
            "run_id": run_id,
            "repository": str(root),
            "workstream": initial_state.workstream_id,
            "task": initial_state.task_id,
            "epoch": initial_state.epoch_id,
            "role": initial_state.current_role,
            "rotate_input_tokens": options.rotate_input_tokens,
            "rotation_soft_input_tokens": options.rotation_soft_input_tokens,
            "max_fresh_input_tokens": options.max_fresh_input_tokens,
            "max_turns_per_epoch": options.max_turns_per_epoch,
            "max_transitions": options.max_transitions,
        },
    )

    def finish(
        state: ActiveState,
        status: str,
        reason: str,
        exit_code: int,
    ) -> SupervisorResult:
        return _finish(
            summary,
            store,
            state,
            status,
            reason,
            exit_code,
            event_sink=event_sink,
        )

    initial_plan = _context_plan(root, options, initial_state)
    _record_context_plan(store, event_sink, initial_plan, scope="initial")
    _append_plan_warnings(summary, initial_plan)
    if options.enforce_context_budget and not initial_plan.ok:
        return finish(initial_state, STATUS_FAILED, _context_failure(initial_plan), 27)

    if options.dry_run:
        decision = decide_continuation(initial_state)
        summary.status = STATUS_DRY_RUN
        summary.reason = ",".join(decision.reasons)
        summary.final_task = initial_state.task_id
        summary.count_transition(decision.action)
        summary.ended_at = utc_now()
        _record_event(
            store,
            event_sink,
            {"type": "dry_run", "action": decision.action, "reasons": list(decision.reasons)},
        )
        store.save_summary(summary)
        return SupervisorResult(STATUS_DRY_RUN, summary.reason, store.summary_path, run_id, 0)

    doctor_checked = False
    thread_id: str | None = None
    thread_turns = 0
    force_rotate_reason = ""
    last_active_signature = _active_signature(root)
    transition_count = 0

    try:
        with RuntimeLock.for_root(root):
            while transition_count < options.max_transitions:
                state = parse_active(root)
                decision = decide_continuation(state)
                summary.count_transition(decision.action)
                _record_event(
                    store,
                    event_sink,
                    {
                        "type": "transition",
                        "action": decision.action,
                        "reasons": list(decision.reasons),
                        "declared_decision": decision.declared_decision,
                        "task": state.task_id,
                        "epoch": state.epoch_id,
                        "role": state.current_role,
                        "human_gate": state.human_gate or None,
                    },
                )

                if decision.action == ACTION_COMPLETE:
                    return finish(state, STATUS_COMPLETE, "WORKSTREAM_COMPLETE", 0)

                if decision.action == ACTION_PAUSE:
                    response = gate_resolver(state) if gate_resolver else None
                    if response:
                        doctor_failure = _check_adapter_once(
                            adapter,
                            store,
                            summary,
                            doctor_checked,
                            event_sink=event_sink,
                        )
                        doctor_checked = True
                        if doctor_failure:
                            return doctor_failure
                        result = _run_gate_resolution(
                            root=root,
                            state=state,
                            response=response,
                            adapter=adapter,
                            store=store,
                            summary=summary,
                            event_sink=event_sink,
                        )
                        if not result.ok:
                            return finish(
                                state,
                                STATUS_FAILED,
                                f"GATE_RESOLUTION_AGENT_FAILED: {result.error or result.exit_code}",
                                22,
                            )
                        _record_event(
                            store,
                            event_sink,
                            {"type": "repository_verification_started", "scope": "gate"},
                        )
                        verification = verify_repository(root)
                        if not verification.ok:
                            return finish(
                                state,
                                STATUS_FAILED,
                                "GATE_RESOLUTION_STATE_INVALID: "
                                + "; ".join(verification.errors),
                                23,
                            )
                        _record_event(
                            store,
                            event_sink,
                            {"type": "repository_verification_passed", "scope": "gate"},
                        )
                        if _active_signature(root) == last_active_signature:
                            return finish(
                                state,
                                STATUS_FAILED,
                                "GATE_RESOLUTION_DID_NOT_ADVANCE_STATE",
                                21,
                            )
                        last_active_signature = _active_signature(root)
                        summary.checkpoints_observed += 1
                        _record_event(
                            store,
                            event_sink,
                            {
                                "type": "checkpoint_observed",
                                "checkpoint": summary.checkpoints_observed,
                                "task": state.task_id,
                                "scope": "gate",
                            },
                        )
                        thread_id = None
                        thread_turns = 0
                        force_rotate_reason = "HUMAN_GATE_BOUNDARY"
                        transition_count += 1
                        continue

                    if options.wait_on_pause:
                        changed = _wait_for_state_change(
                            root, last_active_signature, options.poll_seconds
                        )
                        if not changed:
                            return finish(state, STATUS_PAUSED, "PAUSE_INTERRUPTED", 20)
                        last_active_signature = _active_signature(root)
                        thread_id = None
                        thread_turns = 0
                        force_rotate_reason = "PAUSE_RESOLVED"
                        transition_count += 1
                        continue

                    summary.human_gate = state.human_gate
                    return finish(
                        state,
                        STATUS_PAUSED,
                        ",".join(decision.reasons),
                        20,
                    )

                fresh = (
                    decision.action == ACTION_ROTATE
                    or thread_id is None
                    or bool(force_rotate_reason)
                )
                if fresh:
                    thread_id = None
                    thread_turns = 0
                    summary.runtime_epochs += 1
                    summary.fresh_turns += 1
                    mode = "fresh"
                    rotate_reason = force_rotate_reason or ",".join(decision.reasons)
                    _record_event(
                        store,
                        event_sink,
                        {
                            "type": "runtime_epoch_started",
                            "runtime_epoch": summary.runtime_epochs,
                            "reason": rotate_reason,
                            "declared_epoch": state.epoch_id,
                            "role": state.current_role or state.next_role,
                        },
                    )
                    force_rotate_reason = ""
                else:
                    summary.resumed_turns += 1
                    mode = "continue"

                doctor_failure = _check_adapter_once(
                    adapter,
                    store,
                    summary,
                    doctor_checked,
                    event_sink=event_sink,
                )
                doctor_checked = True
                if doctor_failure:
                    return doctor_failure

                plan = _context_plan(root, options, state)
                _record_context_plan(store, event_sink, plan, scope="turn")
                _append_plan_warnings(summary, plan)
                if options.enforce_context_budget and not plan.ok:
                    return finish(state, STATUS_FAILED, _context_failure(plan), 27)

                prompt = _supervised_prompt(root, mode)
                before_signature = _active_signature(root)
                summary.agent_turns += 1
                thread_turns += 1
                environment = {
                    "RSAW_SUPERVISED": "1",
                    "RSAW_RUN_ID": run_id,
                    "RSAW_RUNTIME_EPOCH": str(summary.runtime_epochs),
                    "RSAW_TASK_ID": state.task_id,
                    "RSAW_ROLE": state.current_role or state.next_role,
                    "RSAW_STABLE_PREFIX": plan.stable_fingerprint,
                }
                _record_event(
                    store,
                    event_sink,
                    {
                        "type": "agent_turn_started",
                        "turn": summary.agent_turns,
                        "runtime_epoch": summary.runtime_epochs,
                        "mode": mode,
                        "fresh": fresh,
                        "task": state.task_id,
                        "role": state.current_role or state.next_role,
                    },
                )
                result = adapter.run_turn(
                    prompt=prompt,
                    root=root,
                    run_dir=store.run_dir,
                    turn_index=summary.agent_turns,
                    thread_id=thread_id,
                    environment=environment,
                )
                summary.total_usage = summary.total_usage + result.usage
                summary.latest_thread_id = result.thread_id
                summary.last_event_path = (
                    str(result.events_path.relative_to(root)) if result.events_path else ""
                )
                summary.last_message_path = (
                    str(result.last_message_path.relative_to(root))
                    if result.last_message_path
                    else ""
                )
                _record_event(
                    store,
                    event_sink,
                    {
                        "type": "agent_turn_terminal",
                        "ok": result.ok,
                        "exit_code": result.exit_code,
                        "thread_id": result.thread_id,
                        "fresh": fresh,
                        "usage": result.usage.to_dict(),
                        "latest_turn_usage": result.latest_turn_usage.to_dict(),
                        "event_count": result.event_count,
                        "error": result.error or None,
                    },
                )
                store.save_summary(summary)

                if not result.ok:
                    return finish(
                        state,
                        STATUS_FAILED,
                        f"AGENT_TURN_FAILED: {result.error or result.exit_code}",
                        22,
                    )

                _record_event(
                    store,
                    event_sink,
                    {"type": "repository_verification_started", "scope": "checkpoint"},
                )
                verification = verify_repository(root)
                if not verification.ok:
                    return finish(
                        state,
                        STATUS_FAILED,
                        "REPOSITORY_STATE_INVALID: " + "; ".join(verification.errors),
                        23,
                    )
                _record_event(
                    store,
                    event_sink,
                    {"type": "repository_verification_passed", "scope": "checkpoint"},
                )

                after_signature = _active_signature(root)
                if after_signature == before_signature:
                    return finish(state, STATUS_FAILED, "ACTIVE_STATE_NOT_ADVANCED", 21)
                summary.checkpoints_observed += 1
                last_active_signature = after_signature
                thread_id = result.thread_id
                transition_count += 1
                _record_event(
                    store,
                    event_sink,
                    {
                        "type": "checkpoint_observed",
                        "checkpoint": summary.checkpoints_observed,
                        "task": state.task_id,
                        "next_task": parse_active(root).task_id,
                    },
                )
                store.save_summary(summary)

                if (
                    options.max_total_input_tokens
                    and summary.total_usage.input_tokens >= options.max_total_input_tokens
                ):
                    return finish(
                        parse_active(root),
                        STATUS_LIMIT_REACHED,
                        "MAX_TOTAL_INPUT_TOKENS",
                        24,
                    )

                rotation = evaluate_rotation(
                    usage=result.latest_turn_usage,
                    thread_turns=thread_turns,
                    max_turns_per_epoch=options.max_turns_per_epoch,
                    hard_input_tokens=options.rotate_input_tokens,
                    soft_input_tokens=options.rotation_soft_input_tokens,
                    max_fresh_input_tokens=options.max_fresh_input_tokens,
                    min_cache_reuse_ratio=options.min_cache_reuse_ratio,
                )
                _record_event(
                    store,
                    event_sink,
                    {"type": "rotation_evaluated", **rotation.to_dict()},
                )
                if rotation.rotate:
                    force_rotate_reason = rotation.reason
                    _record_event(
                        store,
                        event_sink,
                        {"type": "rotation_scheduled", **rotation.to_dict()},
                    )

            return finish(
                parse_active(root),
                STATUS_LIMIT_REACHED,
                "MAX_TRANSITIONS",
                24,
            )
    except RuntimeLockError as exc:
        return finish(
            _safe_state(root, initial_state),
            STATUS_FAILED,
            f"SUPERVISOR_LOCKED: {exc}",
            25,
        )
    except KeyboardInterrupt:
        return finish(
            _safe_state(root, initial_state),
            STATUS_PAUSED,
            "SUPERVISOR_INTERRUPTED",
            20,
        )
    except Exception as exc:  # pragma: no cover
        return finish(
            _safe_state(root, initial_state),
            STATUS_FAILED,
            f"SUPERVISOR_EXCEPTION: {type(exc).__name__}: {exc}",
            26,
        )


def _context_plan(root: Path, options: SupervisorOptions, state: ActiveState) -> ContextPlan:
    return build_context_plan(
        root,
        budget_tokens=options.bootstrap_token_budget,
        max_files=options.max_context_files,
        max_file_bytes=options.max_context_file_bytes,
        include_workstream_spec=options.include_workstream_spec,
        state=state,
    )


def _record_context_plan(
    store: RuntimeStore,
    event_sink: RuntimeEventSink | None,
    plan: ContextPlan,
    *,
    scope: str,
) -> None:
    _record_event(store, event_sink, {"type": "context_plan", "scope": scope, **plan.to_dict()})


def _append_plan_warnings(summary: RuntimeSummary, plan: ContextPlan) -> None:
    for warning in (*plan.errors, *plan.warnings):
        if warning not in summary.warnings:
            summary.warnings.append(warning)


def _context_failure(plan: ContextPlan) -> str:
    details = list(plan.errors)
    if not plan.within_budget:
        details.append(
            f"BOOTSTRAP_TOKEN_BUDGET_EXCEEDED: {plan.total_tokens}>{plan.budget_tokens}"
        )
    return "CONTEXT_PLAN_INVALID: " + "; ".join(details)


def _check_adapter_once(
    adapter: AgentAdapter,
    store: RuntimeStore,
    summary: RuntimeSummary,
    already_checked: bool,
    *,
    event_sink: RuntimeEventSink | None = None,
) -> SupervisorResult | None:
    if already_checked:
        return None
    doctor = adapter.doctor()
    _record_event(store, event_sink, {"type": "adapter_doctor", **doctor.to_dict()})
    if doctor.ok:
        return None
    summary.status = STATUS_FAILED
    summary.reason = "ADAPTER_DOCTOR_FAILED: " + "; ".join(doctor.errors)
    summary.ended_at = utc_now()
    store.save_summary(summary)
    _notify_event(
        event_sink,
        {"type": "supervisor_terminal", "status": STATUS_FAILED, "reason": summary.reason},
    )
    return SupervisorResult(
        STATUS_FAILED, summary.reason, store.summary_path, summary.run_id, 22
    )


def _run_gate_resolution(
    *,
    root: Path,
    state: ActiveState,
    response: str,
    adapter: AgentAdapter,
    store: RuntimeStore,
    summary: RuntimeSummary,
    event_sink: RuntimeEventSink | None = None,
):
    summary.runtime_epochs += 1
    summary.agent_turns += 1
    summary.fresh_turns += 1
    response_hash = hashlib.sha256(response.encode("utf-8")).hexdigest()
    _record_event(
        store,
        event_sink,
        {
            "type": "human_gate_response",
            "gate": state.human_gate,
            "response_sha256": response_hash,
        },
    )
    base = render_prompt(root, role=None, mode="fresh")
    instruction = f"""

RSAW HUMAN-GATE RESOLUTION TURN

The human supplied this exact response to the active gate:
{json.dumps(response)}

Apply the response only through the repository's existing governance and safety
mechanisms. Verify all authoritative bindings. Resolve or reject the gate,
persist evidence, update ACTIVE.md, and set the next transition. Do not execute
the next role or task in this turn. Do not print a prompt for human relay; the
RSAW supervisor will rotate automatically.
"""
    _record_event(
        store,
        event_sink,
        {
            "type": "agent_turn_started",
            "turn": summary.agent_turns,
            "runtime_epoch": summary.runtime_epochs,
            "mode": "fresh",
            "fresh": True,
            "task": state.task_id,
            "role": "GateResolver",
        },
    )
    result = adapter.run_turn(
        prompt=base + instruction,
        root=root,
        run_dir=store.run_dir,
        turn_index=summary.agent_turns,
        thread_id=None,
        environment={
            "RSAW_SUPERVISED": "1",
            "RSAW_GATE_RESOLUTION": "1",
            "RSAW_RUN_ID": summary.run_id,
            "RSAW_TASK_ID": state.task_id,
        },
    )
    summary.total_usage = summary.total_usage + result.usage
    summary.latest_thread_id = result.thread_id
    summary.last_event_path = (
        str(result.events_path.relative_to(root)) if result.events_path else ""
    )
    summary.last_message_path = (
        str(result.last_message_path.relative_to(root))
        if result.last_message_path
        else ""
    )
    _record_event(
        store,
        event_sink,
        {
            "type": "gate_resolution_turn_terminal",
            "ok": result.ok,
            "exit_code": result.exit_code,
            "usage": result.usage.to_dict(),
            "latest_turn_usage": result.latest_turn_usage.to_dict(),
            "error": result.error or None,
        },
    )
    store.save_summary(summary)
    return result


def _supervised_prompt(root: Path, mode: str) -> str:
    return render_prompt(root, role=None, mode=mode) + """

RSAW RUNTIME SUPERVISOR IS ACTIVE

Complete exactly one durable repository checkpoint in this turn. Do not ask the
human to copy or relay a next prompt. Do not spawn a replacement model context.
Update ACTIVE.md with the next task and transition. The supervisor will reuse,
rotate, pause, or complete the workstream after verifying repository state.
If human or external action is required, record a Human Gate and PAUSE/STOP
metadata rather than busy-waiting or bypassing authority.
"""


def _active_signature(root: Path) -> str:
    return hashlib.sha256((root / "ACTIVE.md").read_bytes()).hexdigest()


def _safe_state(root: Path, fallback: ActiveState) -> ActiveState:
    try:
        return parse_active(root)
    except Exception:
        return fallback


def _wait_for_state_change(root: Path, previous: str, poll_seconds: float) -> bool:
    try:
        while True:
            time.sleep(poll_seconds)
            if _active_signature(root) != previous:
                return True
    except KeyboardInterrupt:
        return False


def _finish(
    summary: RuntimeSummary,
    store: RuntimeStore,
    state: ActiveState,
    status: str,
    reason: str,
    exit_code: int,
    *,
    event_sink: RuntimeEventSink | None = None,
) -> SupervisorResult:
    summary.status = status
    summary.reason = reason
    summary.final_task = state.task_id
    summary.human_gate = state.human_gate
    summary.ended_at = utc_now()
    _record_event(
        store,
        event_sink,
        {
            "type": "supervisor_terminal",
            "status": status,
            "reason": reason,
            "final_task": state.task_id,
            "human_gate": state.human_gate or None,
        },
    )
    store.save_summary(summary)
    return SupervisorResult(status, reason, store.summary_path, summary.run_id, exit_code)


def _record_event(
    store: RuntimeStore,
    event_sink: RuntimeEventSink | None,
    event: dict[str, Any],
) -> None:
    store.append_event(event)
    _notify_event(event_sink, event)


def _notify_event(event_sink: RuntimeEventSink | None, event: dict[str, Any]) -> None:
    if event_sink is None:
        return
    try:
        event_sink(event)
    except Exception:
        return
''',
)

write(
    "src/repo_state_agent/cli.py",
    '''from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

from .archive import archive_active
from .continuation import decide_continuation
from .footprint import measure_bootstrap
from .model import ActiveState
from .parsing import parse_active
from .prompts import VALID_MODES, VALID_ROLES, render_prompt
from .runtime.codex import CodexAdapter, CodexEventSink
from .runtime.config import RuntimeConfig, load_runtime_config
from .runtime.context import build_context_plan
from .runtime.report import efficiency_view, load_runtime_summary
from .runtime.supervisor import options_from_config, supervise
from .runtime.tui import LiveDashboard, preview_dashboard, should_use_tui
from .scaffold import initialize_repository
from .verify import verify_repository


def _root(value: str) -> Path:
    return Path(value).expanduser().resolve()


def cmd_init(args: argparse.Namespace) -> int:
    created, skipped = initialize_repository(_root(args.path), force=args.force)
    for path in created:
        print(f"CREATE {path}")
    for path in skipped:
        print(f"SKIP   {path}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    result = verify_repository(_root(args.path), args.max_lines, args.max_bytes)
    payload = {"ok": result.ok, "errors": result.errors, "warnings": result.warnings}
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("PASS" if result.ok else "FAIL")
        for warning in result.warnings:
            print(f"WARNING: {warning}")
        for error in result.errors:
            print(f"ERROR: {error}")
    return 0 if result.ok else 1


def cmd_footprint(args: argparse.Namespace) -> int:
    root = _root(args.path)
    rows = measure_bootstrap(root, include_required=not args.base_only)
    total = {
        "lines": sum(row.lines for row in rows),
        "bytes": sum(row.bytes for row in rows),
        "chars": sum(row.chars for row in rows),
        "approx_tokens": sum(row.approx_tokens for row in rows),
    }
    if args.json:
        print(
            json.dumps(
                {
                    "files": [
                        {
                            "path": str(row.path.relative_to(root)),
                            "lines": row.lines,
                            "bytes": row.bytes,
                            "chars": row.chars,
                            "approx_tokens": row.approx_tokens,
                        }
                        for row in rows
                    ],
                    "total": total,
                    "token_estimate": "approximate chars/4",
                },
                indent=2,
            )
        )
    else:
        print(f"{'PATH':50} {'LINES':>7} {'BYTES':>9} {'TOKENS~':>9}")
        for row in rows:
            rel = str(row.path.relative_to(root))
            print(f"{rel:50} {row.lines:7d} {row.bytes:9d} {row.approx_tokens:9d}")
        print("-" * 79)
        print(
            f"{'TOTAL':50} {total['lines']:7d} {total['bytes']:9d} "
            f"{total['approx_tokens']:9d}"
        )
        print("Token estimate is approximate: UTF-8 text characters / 4.")
    if args.max_tokens is not None and total["approx_tokens"] > args.max_tokens:
        return 1
    return 0


def cmd_context(args: argparse.Namespace) -> int:
    root = _root(args.path)
    config = load_runtime_config(root)
    plan = build_context_plan(
        root,
        budget_tokens=config.bootstrap_token_budget,
        max_files=config.max_context_files,
        max_file_bytes=config.max_context_file_bytes,
        include_workstream_spec=config.include_workstream_spec,
    )
    payload = plan.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"{'CATEGORY':10} {'TOKENS~':>9} {'BYTES':>9}  PATH")
        for document in plan.documents:
            print(
                f"{document.category:10} {document.approx_tokens:9d} "
                f"{document.bytes:9d}  {document.path}"
            )
        print("-" * 80)
        print(f"TOTAL       {plan.total_tokens:9d} / {plan.budget_tokens} tokens")
        print(f"STABLE      {plan.stable_tokens:9d} tokens")
        print(f"DYNAMIC     {plan.dynamic_tokens:9d} tokens")
        print(f"PREFIX      {plan.stable_fingerprint[:16]}")
        print(f"DYNAMIC     {plan.dynamic_fingerprint[:16]}")
        print(f"STATUS      {'PASS' if plan.ok else 'REVIEW'}")
        for warning in plan.warnings:
            print(f"WARNING: {warning}")
        for error in plan.errors:
            print(f"ERROR: {error}")
    return 1 if args.strict and not plan.ok else 0


def cmd_archive(args: argparse.Namespace) -> int:
    target = archive_active(_root(args.path), args.label)
    print(target)
    return 0


def cmd_checkpoint(args: argparse.Namespace) -> int:
    root = _root(args.path)
    state = parse_active(root)
    label = args.label or f"{state.task_id or 'task'}-checkpoint"
    target = archive_active(root, label)
    print(target)
    return 0


def _state_payload(root: Path) -> dict[str, object]:
    state = parse_active(root)
    decision = decide_continuation(state)
    return {
        "workstream": state.workstream_id or None,
        "workstream_spec": (
            str(state.workstream_spec.relative_to(root)) if state.workstream_spec else None
        ),
        "epoch": state.epoch_id or None,
        "current_role": state.current_role or None,
        "active_task": state.task_id,
        "active_task_spec": str(state.task_spec.relative_to(root)),
        "declared_continuation": state.continuation,
        "runtime_action": decision.action,
        "continuation_reasons": list(decision.reasons),
        "next_task": state.next_task_id or None,
        "next_task_spec": (
            str(state.next_task_spec.relative_to(root)) if state.next_task_spec else None
        ),
        "next_role": state.next_role,
        "human_gate": state.human_gate or None,
        "next_action": state.next_action,
        "stop_condition": state.stop_condition,
    }


def cmd_status(args: argparse.Namespace) -> int:
    root = _root(args.path)
    payload = _state_payload(root)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"WORKSTREAM  {payload['workstream'] or 'classic'}")
        print(f"EPOCH       {payload['epoch'] or 'fresh-task'}")
        print(f"ROLE        {payload['current_role'] or payload['next_role']}")
        print(f"TASK        {payload['active_task']} ({payload['active_task_spec']})")
        print(f"ACTION      {payload['runtime_action']}")
        print(f"REASON      {', '.join(payload['continuation_reasons'])}")
        print(f"NEXT TASK   {payload['next_task'] or '-'}")
        print(f"NEXT ROLE   {payload['next_role']}")
        print(f"HUMAN GATE  {payload['human_gate'] or 'none'}")
    return 0


def cmd_next(args: argparse.Namespace) -> int:
    payload = _state_payload(_root(args.path))
    result = {
        "action": payload["runtime_action"],
        "declared_decision": payload["declared_continuation"],
        "reasons": payload["continuation_reasons"],
        "next_task": payload["next_task"],
        "next_task_spec": payload["next_task_spec"],
        "next_role": payload["next_role"],
        "human_gate": payload["human_gate"],
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["action"])
        print(f"Reason: {', '.join(result['reasons'])}")
        if result["next_task"]:
            print(f"Next task: {result['next_task']} ({result['next_task_spec']})")
        print(f"Next role: {result['next_role']}")
        if result["human_gate"]:
            print(f"Human gate: {result['human_gate']}")
    return 0


def cmd_prompt(args: argparse.Namespace) -> int:
    print(render_prompt(_root(args.path), args.role, args.mode))
    return 0


def _codex_adapter(
    args: argparse.Namespace,
    config: RuntimeConfig,
    *,
    event_sink: CodexEventSink | None = None,
    quiet_override: bool = False,
) -> CodexAdapter:
    return CodexAdapter(
        binary=args.codex_bin or config.codex_binary,
        model=args.model if args.model is not None else config.model,
        profile=args.profile if args.profile is not None else config.profile,
        sandbox=args.sandbox or config.sandbox,
        approve_for_me=bool(args.approve_for_me or config.approve_for_me),
        quiet=bool(getattr(args, "quiet", False) or quiet_override),
        event_sink=event_sink,
    )


def cmd_doctor(args: argparse.Namespace) -> int:
    root = _root(args.path)
    config = load_runtime_config(root)
    result = _codex_adapter(args, config).doctor()
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print("PASS" if result.ok else "FAIL")
        print(f"Adapter: {result.adapter}")
        print(f"Binary: {result.binary}")
        print(f"Version: {result.version or 'unknown'}")
        if result.capabilities:
            print(f"Capabilities: {', '.join(result.capabilities)}")
        for warning in result.warnings:
            print(f"WARNING: {warning}")
        for error in result.errors:
            print(f"ERROR: {error}")
    return 0 if result.ok else 1


def _interactive_gate(state: ActiveState) -> str | None:
    print("\nRSAW WORKSTREAM PAUSED")
    print(f"Human gate: {state.human_gate or 'unspecified'}")
    print(f"Task: {state.task_id}")
    print("Enter the exact human response for the repository gate.")
    print("Use :quit to leave the supervisor without changing repository state.")
    response = input("rsaw> ").strip()
    return None if not response or response == ":quit" else response


def _load_summary_for_result(root: Path, run_id: str) -> dict[str, Any] | None:
    if not run_id:
        return None
    try:
        return load_runtime_summary(root, run_id)
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        return None


def cmd_run(args: argparse.Namespace) -> int:
    root = _root(args.path)
    config = load_runtime_config(root)
    config = replace(
        config,
        codex_binary=args.codex_bin or config.codex_binary,
        model=args.model if args.model is not None else config.model,
        profile=args.profile if args.profile is not None else config.profile,
        sandbox=args.sandbox or config.sandbox,
        approve_for_me=bool(args.approve_for_me or config.approve_for_me),
        max_transitions=args.max_transitions or config.max_transitions,
        max_turns_per_epoch=args.max_turns_per_epoch or config.max_turns_per_epoch,
        rotate_input_tokens=(
            args.rotate_input_tokens
            if args.rotate_input_tokens is not None
            else config.rotate_input_tokens
        ),
        rotation_soft_input_tokens=(
            args.rotation_soft_input_tokens
            if args.rotation_soft_input_tokens is not None
            else config.rotation_soft_input_tokens
        ),
        max_fresh_input_tokens=(
            args.max_fresh_input_tokens
            if args.max_fresh_input_tokens is not None
            else config.max_fresh_input_tokens
        ),
        min_cache_reuse_ratio=(
            args.min_cache_reuse_ratio
            if args.min_cache_reuse_ratio is not None
            else config.min_cache_reuse_ratio
        ),
        max_total_input_tokens=(
            args.max_total_input_tokens
            if args.max_total_input_tokens is not None
            else config.max_total_input_tokens
        ),
        wait_on_pause=bool(args.wait_on_pause or config.wait_on_pause),
        enforce_context_budget=bool(
            args.enforce_context_budget or config.enforce_context_budget
        ),
    )
    options = options_from_config(config, dry_run=args.dry_run, quiet=args.quiet)
    interactive = (
        not args.no_interactive_gates
        and config.interactive_gates
        and sys.stdin.isatty()
        and not args.dry_run
    )
    use_tui = should_use_tui(
        force=bool(args.tui),
        disable=bool(args.no_tui),
        json_output=bool(args.json),
        quiet=bool(args.quiet),
        dry_run=bool(args.dry_run),
    )
    dashboard = (
        LiveDashboard(root, rotate_input_tokens=config.rotate_input_tokens)
        if use_tui
        else None
    )
    adapter = _codex_adapter(
        args,
        config,
        event_sink=dashboard.handle_codex_event if dashboard else None,
        quiet_override=bool(dashboard),
    )
    gate_resolver = _interactive_gate if interactive else None
    if dashboard and gate_resolver:
        gate_resolver = dashboard.gate_resolver(gate_resolver)

    if dashboard:
        with dashboard:
            result = supervise(
                root,
                adapter,
                options,
                gate_resolver=gate_resolver,
                event_sink=dashboard.handle_supervisor_event,
            )
            dashboard.finalize(
                status=result.status,
                reason=result.reason,
                summary_path=(
                    str(result.summary_path.relative_to(root)) if result.summary_path else ""
                ),
                summary=_load_summary_for_result(root, result.run_id),
            )
            dashboard.settle()
    else:
        result = supervise(root, adapter, options, gate_resolver=gate_resolver)

    payload = {
        "status": result.status,
        "reason": result.reason,
        "run_id": result.run_id,
        "summary_path": (
            str(result.summary_path.relative_to(root)) if result.summary_path else None
        ),
        "exit_code": result.exit_code,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    elif not dashboard:
        print(f"RSAW {result.status}: {result.reason}")
        if result.summary_path:
            print(f"Summary: {result.summary_path}")
    return result.exit_code


def cmd_preview(args: argparse.Namespace) -> int:
    root = _root(args.path)
    verification = verify_repository(root)
    if not verification.ok:
        for error in verification.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    config = load_runtime_config(root)
    preview_dashboard(root, rotate_input_tokens=config.rotate_input_tokens, seconds=args.seconds)
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    root = _root(args.path)
    try:
        summary = load_runtime_summary(root, args.run_id)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    view = efficiency_view(summary)
    if args.json:
        print(json.dumps(view, indent=2))
    else:
        print(f"RUN             {view['run_id']}")
        print(f"STATUS          {view['status']} ({view['reason']})")
        print(f"WORKSTREAM      {view['workstream']}")
        print(f"TURNS           {view['agent_turns']}")
        print(f"EPOCHS          {view['runtime_epochs']}")
        print(f"FRESH/RESUME    {view['fresh_turns']}/{view['resumed_turns']}")
        print(f"CHECKPOINTS     {view['checkpoints_observed']}")
        print(f"INPUT TOKENS    {view['usage'].get('input_tokens', 0)}")
        print(f"CACHED INPUT    {view['usage'].get('cached_input_tokens', 0)}")
        print(f"FRESH INPUT     {view['fresh_input_tokens']}")
        print(f"CACHE REUSE     {view['cache_reuse_ratio']}")
        print(f"INPUT/CHECK     {view['input_tokens_per_checkpoint']}")
        print(f"FRESH/CHECK     {view['fresh_input_tokens_per_checkpoint']}")
        print(f"OUTPUT          {view['usage'].get('output_tokens', 0)}")
    return 0


def _add_codex_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--codex-bin")
    parser.add_argument("--model")
    parser.add_argument("--profile")
    parser.add_argument("--sandbox")
    parser.add_argument("--approve-for-me", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rsaw", description="Repository-State Agent Workflow"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Initialize a plug-and-play RSAW workstream")
    init.add_argument("path", nargs="?", default=".")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    verify = sub.add_parser("verify", help="Verify ACTIVE.md and its references")
    verify.add_argument("path", nargs="?", default=".")
    verify.add_argument("--max-lines", type=int, default=140)
    verify.add_argument("--max-bytes", type=int, default=12_288)
    verify.add_argument("--json", action="store_true")
    verify.set_defaults(func=cmd_verify)

    status = sub.add_parser("status", help="Show the active workstream, task, and action")
    status.add_argument("path", nargs="?", default=".")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_status)

    next_cmd = sub.add_parser("next", help="Evaluate the next runtime action")
    next_cmd.add_argument("path", nargs="?", default=".")
    next_cmd.add_argument("--json", action="store_true")
    next_cmd.set_defaults(func=cmd_next)

    footprint = sub.add_parser("footprint", help="Estimate bootstrap context footprint")
    footprint.add_argument("path", nargs="?", default=".")
    footprint.add_argument("--base-only", action="store_true")
    footprint.add_argument("--max-tokens", type=int)
    footprint.add_argument("--json", action="store_true")
    footprint.set_defaults(func=cmd_footprint)

    context = sub.add_parser("context", help="Inspect the ordered cache-aware context plan")
    context.add_argument("path", nargs="?", default=".")
    context.add_argument("--json", action="store_true")
    context.add_argument("--strict", action="store_true")
    context.set_defaults(func=cmd_context)

    archive = sub.add_parser("archive", help="Archive ACTIVE.md")
    archive.add_argument("path", nargs="?", default=".")
    archive.add_argument("--label", required=True)
    archive.set_defaults(func=cmd_archive)

    checkpoint = sub.add_parser("checkpoint", help="Archive the current handoff checkpoint")
    checkpoint.add_argument("path", nargs="?", default=".")
    checkpoint.add_argument("--label")
    checkpoint.set_defaults(func=cmd_checkpoint)

    prompt = sub.add_parser("prompt", help="Render the active minimal prompt")
    prompt.add_argument("path", nargs="?", default=".")
    prompt.add_argument("--role", choices=sorted(VALID_ROLES))
    prompt.add_argument("--mode", choices=sorted(VALID_MODES), default="auto")
    prompt.set_defaults(func=cmd_prompt)

    doctor = sub.add_parser("doctor", help="Check runtime adapter compatibility")
    doctor.add_argument("path", nargs="?", default=".")
    doctor.add_argument("--agent", choices=["codex"], default="codex")
    doctor.add_argument("--json", action="store_true")
    _add_codex_options(doctor)
    doctor.set_defaults(func=cmd_doctor)

    run = sub.add_parser("run", help="Supervise a long-lived workstream")
    run.add_argument("path", nargs="?", default=".")
    run.add_argument("--agent", choices=["codex"], default="codex")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--json", action="store_true")
    run.add_argument("--quiet", action="store_true")
    tui = run.add_mutually_exclusive_group()
    tui.add_argument("--tui", action="store_true", help="Force the live terminal dashboard")
    tui.add_argument("--no-tui", action="store_true", help="Use plain log output")
    run.add_argument("--no-interactive-gates", action="store_true")
    run.add_argument("--wait-on-pause", action="store_true")
    run.add_argument("--max-transitions", type=int)
    run.add_argument("--max-turns-per-epoch", type=int)
    run.add_argument("--rotate-input-tokens", type=int)
    run.add_argument("--rotation-soft-input-tokens", type=int)
    run.add_argument("--max-fresh-input-tokens", type=int)
    run.add_argument("--min-cache-reuse-ratio", type=float)
    run.add_argument("--max-total-input-tokens", type=int)
    run.add_argument("--enforce-context-budget", action="store_true")
    _add_codex_options(run)
    run.set_defaults(func=cmd_run)

    preview = sub.add_parser(
        "preview", help="Preview the live terminal dashboard without launching an agent"
    )
    preview.add_argument("path", nargs="?", default=".")
    preview.add_argument("--seconds", type=float, default=6.0)
    preview.set_defaults(func=cmd_preview)

    report = sub.add_parser("report", help="Report runtime context and transition efficiency")
    report.add_argument("path", nargs="?", default=".")
    report.add_argument("--run-id")
    report.add_argument("--json", action="store_true")
    report.set_defaults(func=cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
''',
)

write(
    "src/repo_state_agent/templates/CONFIG.json",
    '''{
  "schema_version": 2,
  "runtime": {
    "adapter": "codex",
    "codex_binary": "codex",
    "sandbox": "workspace-write",
    "approve_for_me": false,
    "max_transitions": 100,
    "max_turns_per_epoch": 6,
    "max_total_input_tokens": 5000000,
    "interactive_gates": true,
    "wait_on_pause": false,
    "rotation": {
      "soft_input_tokens": 48000,
      "hard_input_tokens": 60000,
      "max_fresh_input_tokens": 18000,
      "min_cache_reuse_ratio": 0.5
    },
    "context": {
      "bootstrap_token_budget": 15000,
      "max_files": 12,
      "max_file_bytes": 262144,
      "include_workstream_spec": false,
      "enforce_budget": false
    }
  }
}
''',
)

write(
    ".rsaw/config.json",
    '''{
  "schema_version": 2,
  "runtime": {
    "adapter": "codex",
    "codex_binary": "codex",
    "sandbox": "workspace-write",
    "approve_for_me": false,
    "max_transitions": 100,
    "max_turns_per_epoch": 6,
    "max_total_input_tokens": 5000000,
    "interactive_gates": true,
    "wait_on_pause": false,
    "rotation": {
      "soft_input_tokens": 48000,
      "hard_input_tokens": 60000,
      "max_fresh_input_tokens": 18000,
      "min_cache_reuse_ratio": 0.5
    },
    "context": {
      "bootstrap_token_budget": 15000,
      "max_files": 12,
      "max_file_bytes": 262144,
      "include_workstream_spec": false,
      "enforce_budget": false
    }
  }
}
''',
)

write(
    "src/repo_state_agent/templates/AGENTS.md",
    '''# Agent Policy

## Source of Truth

Repository state overrides conversation history.

Use this authority order:

1. accepted decisions and immutable contracts;
2. executable schemas, tests, and validation;
3. active task specification;
4. `ACTIVE.md` continuation state;
5. conversation context.

## Cache-Aware Bootstrap

Read the ordered context plan produced by `rsaw context .`.

- Stable prefix: policy and other rarely changing authority.
- Dynamic authority: `ACTIVE.md`, the active task, and bounded required reads.
- In a continued epoch, do not reread the stable prefix unless its fingerprint changed.
- Expand context only for evidence required by the current checkpoint.

## Persistent Workstream

The workstream may span many tasks and context epochs. Every task must produce a
durable checkpoint before the next task begins.

When the RSAW supervisor is active, do not ask the human to copy a next-session
prompt. Update `ACTIVE.md`; the supervisor applies the next runtime action.

## Runtime Actions

- `CONTINUE`: reuse the current context for a tightly coupled task.
- `ROTATE`: keep the workstream running in a fresh context.
- `PAUSE`: wait for explicit human or external action.
- `COMPLETE`: terminate the workstream.

## Mandatory Rotation

Use a fresh context for role changes, formal execution/analysis boundaries,
independent review, major decisions, major debugging closure, specification
changes, hard context pressure, fresh-input pressure, or poor cache reuse near the
soft threshold.

## Validation

- `V0`: syntax, lint, exact test during editing;
- `V1`: focused task-checkpoint validation;
- `V2`: one relevant epoch or phase closure;
- `V3`: fresh independent review for critical work.

Validation is a gate, not the product. Add validation only for an observed threat
or explicit contract.

## Runtime Safety

- Do not enable dangerous sandbox or approval bypasses.
- Do not infer authorization, credentials, privilege, or destructive consent.
- Do not automatically retry failed formal or scientific runs.
- Preserve failed evidence and consumed authorizations.
- Ensure `ACTIVE.md` advances after every successful supervised turn.
- Respect transition, turn, context, and token limits.

## Evidence Discipline

Tests establish implementation behavior. Scientific and production claims need a
protocol, provenance, measured evidence, and interpretation boundary. Do not
rewrite raw evidence or hide negative results.

## Handoff

Before a checkpoint, record current state, evidence pointers, blockers, human
gates, active and next task, exact next action, stop condition, current and next
role, and continuation decision. Keep routine narration low.
''',
)

write(
    "AGENTS.md",
    '''# Agent Policy

## Source of Truth

Repository state overrides conversation history.

Use this authority order:

1. accepted decisions and immutable contracts;
2. executable schemas, tests, and validation;
3. active task specification;
4. `ACTIVE.md` continuation state;
5. conversation context.

## Cache-Aware Bootstrap

Read the ordered context plan produced by `rsaw context .`.

- Stable prefix: policy and other rarely changing authority.
- Dynamic authority: `ACTIVE.md`, the active task, and bounded required reads.
- In a continued epoch, do not reread the stable prefix unless its fingerprint changed.
- Expand context only for evidence required by the current checkpoint.

## Persistent Workstream

The workstream may span many tasks and context epochs. Every task must produce a
durable checkpoint before the next task begins.

When the RSAW supervisor is active, do not ask the human to copy a next-session
prompt. Update `ACTIVE.md`; the supervisor applies the next runtime action.

## Runtime Actions

- `CONTINUE`: reuse the current context for a tightly coupled task.
- `ROTATE`: keep the workstream running in a fresh context.
- `PAUSE`: wait for explicit human or external action.
- `COMPLETE`: terminate the workstream.

## Mandatory Rotation

Use a fresh context for role changes, formal execution/analysis boundaries,
independent review, major decisions, major debugging closure, specification
changes, hard context pressure, fresh-input pressure, or poor cache reuse near the
soft threshold.

## Validation

- `V0`: syntax, lint, exact test during editing;
- `V1`: focused task-checkpoint validation;
- `V2`: one relevant epoch or phase closure;
- `V3`: fresh independent review for critical work.

Validation is a gate, not the product. Add validation only for an observed threat
or explicit contract.

## Runtime Safety

- Do not enable dangerous sandbox or approval bypasses.
- Do not infer authorization, credentials, privilege, or destructive consent.
- Do not automatically retry failed formal or scientific runs.
- Preserve failed evidence and consumed authorizations.
- Ensure `ACTIVE.md` advances after every successful supervised turn.
- Respect transition, turn, context, and token limits.

## Evidence Discipline

Tests establish implementation behavior. Scientific and production claims need a
protocol, provenance, measured evidence, and interpretation boundary. Do not
rewrite raw evidence or hide negative results.

## Handoff

Before a checkpoint, record current state, evidence pointers, blockers, human
gates, active and next task, exact next action, stop condition, current and next
role, and continuation decision. Keep routine narration low.
''',
)

write(
    "src/repo_state_agent/templates/ACTIVE.md",
    '''# Active Handoff

## Repository

Branch: main
HEAD: UNKNOWN
Status: inspect before work

## Workstream

ID: W-000
Spec: docs/workstreams/W-000-bootstrap.md

## Context Epoch

ID: E-000
Role: Builder

## Active Task

ID: T-000
Spec: docs/tasks/T-000-bootstrap.md

## Current State

- RSAW has been initialized.
- Project policy and the first real workstream task still need review.

## Evidence

- Repository root identified.

## Required Reads

- AGENTS.md
- ACTIVE.md
- docs/tasks/T-000-bootstrap.md

## Context Contract

Mode: BOUNDED
Stable Prefix: AGENTS.md
Budget: inherit `.rsaw/config.json`

## Do Not Preload

- full repository tree;
- historical logs;
- all decisions;
- archived handoffs.

## Human Gate

None.

## Running or Pending External Work

None.

## Blockers

None.

## Next Exact Action

Customize policy, define the real workstream, and activate the first real task.

## Stop Condition

Project policy, workstream, and first task are actionable and `rsaw verify .` passes.

## Continuation Gate

Decision: ROTATE_REQUIRED
Reason: Bootstrap policy changes should hand off to a fresh project context.

## Next Task

None.

## Next Session Role

Builder

## Recommended Reasoning

Medium

## Last Updated

INITIALIZED
''',
)

write(
    "src/repo_state_agent/templates/TASK.md",
    '''# T-000 — Bootstrap Repository-State Workflow

## Workstream

W-000 — Bootstrap

## Goal

Customize RSAW for this repository and define the first real task.

## Role

Builder

## Blocked By

None.

## Inputs and Authority

- existing repository documentation;
- build and test commands;
- current project priorities.

## Context Budget

- Stable authority: `AGENTS.md`.
- Dynamic authority: `ACTIVE.md` and this task.
- Additional reads must be justified by the active acceptance criterion.
- Inspect with `rsaw context .` before a large checkpoint.

## In Scope

- customize AGENTS.md;
- update the workstream contract;
- update ACTIVE.md;
- define the first real task;
- choose whether the next checkpoint can continue or must rotate.

## Out of Scope

- implementing the product feature itself;
- rewriting all existing documentation.

## Acceptance Criteria

- AGENTS.md contains stable project policy;
- ACTIVE.md is compact and actionable;
- workstream spec exists;
- active task exists;
- continuation decision is explicit;
- `rsaw verify .` passes;
- `rsaw context .` is within the configured bootstrap budget.

## Targeted Validation

```bash
rsaw verify .
rsaw context . --strict
rsaw status .
rsaw next .
```

## Evidence Expected

A clean diff and verified active handoff.

## Continuation Candidate

Rotate after bootstrap because the next task establishes real project work.

## Stop Condition

The first real task is ready for a fresh builder context.
''',
)

write(
    "src/repo_state_agent/templates/CONTEXT_POLICY.md",
    '''# RSAW Context Policy

## Stable Prefix

Keep stable policy before dynamic task state. Stable files should change rarely and
retain a deterministic fingerprint.

## Dynamic Authority

`ACTIVE.md`, the active task, and explicitly required evidence form the dynamic
suffix. Do not preload the repository tree.

## Continue

When the supervisor resumes the same thread, reread dynamic authority only. Reload
the stable prefix only when its fingerprint changes.

## Rotate

Rotate at role/scientific boundaries, hard token pressure, fresh-input pressure,
or low cache reuse near the soft threshold.

## Measurement

Track total input, cached input, fresh input, output, checkpoints, epochs, and
rotations. Optimize fresh input per successful checkpoint, not cache hits alone.
''',
)

write(
    "src/repo_state_agent/scaffold.py",
    '''from __future__ import annotations

from importlib import resources
from pathlib import Path

TEMPLATE_MAP = {
    "AGENTS.md": "AGENTS.md",
    "ACTIVE.md": "ACTIVE.md",
    ".rsaw/config.json": "CONFIG.json",
    ".rsaw/.gitignore": "RSAW_GITIGNORE.txt",
    "docs/workstreams/W-000-bootstrap.md": "WORKSTREAM.md",
    "docs/tasks/T-000-bootstrap.md": "TASK.md",
    "docs/agents/repository-state-workflow.md": "WORKFLOW.md",
    "docs/agents/context-policy.md": "CONTEXT_POLICY.md",
}


def _template_text(name: str) -> str:
    return resources.files("repo_state_agent.templates").joinpath(name).read_text(encoding="utf-8")


def initialize_repository(root: Path, force: bool = False) -> tuple[list[Path], list[Path]]:
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    skipped: list[Path] = []
    for relative, template in TEMPLATE_MAP.items():
        target = root / relative
        if target.exists() and not force:
            skipped.append(target)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_template_text(template), encoding="utf-8")
        created.append(target)
    (root / "docs/handoffs/archive").mkdir(parents=True, exist_ok=True)
    (root / "docs/checkpoints").mkdir(parents=True, exist_ok=True)
    (root / "docs/decisions").mkdir(parents=True, exist_ok=True)
    return created, skipped
''',
)

write(
    "tests/test_context_plan.py",
    '''from __future__ import annotations

from pathlib import Path

from repo_state_agent.runtime.context import build_context_plan


def _repo(root: Path) -> None:
    (root / "docs/tasks").mkdir(parents=True)
    (root / "docs/workstreams").mkdir(parents=True)
    (root / "AGENTS.md").write_text("# Policy\nstable\n", encoding="utf-8")
    (root / "docs/tasks/T-1.md").write_text("# Task\ndynamic\n", encoding="utf-8")
    (root / "docs/tasks/T-2.md").write_text("# Next\n", encoding="utf-8")
    (root / "docs/workstreams/W-1.md").write_text("# Workstream\n", encoding="utf-8")
    (root / "ACTIVE.md").write_text(
        """# Active Handoff

## Workstream
ID: W-1
Spec: docs/workstreams/W-1.md

## Context Epoch
ID: E-1
Role: Builder

## Active Task
ID: T-1
Spec: docs/tasks/T-1.md

## Required Reads
- AGENTS.md
- ACTIVE.md
- docs/tasks/T-1.md

## Human Gate
None.

## Next Exact Action
Do it.

## Stop Condition
Done.

## Continuation Gate
Decision: CONTINUE_ALLOWED
Reason: SAME_TASK

## Next Task
ID: T-2
Spec: docs/tasks/T-2.md

## Next Session Role
Builder

## Recommended Reasoning
Medium
""",
        encoding="utf-8",
    )


def test_context_plan_is_ordered_deduplicated_and_fingerprinted(tmp_path: Path) -> None:
    _repo(tmp_path)
    plan = build_context_plan(tmp_path, budget_tokens=10_000)
    assert [document.path for document in plan.documents] == [
        "AGENTS.md",
        "ACTIVE.md",
        "docs/tasks/T-1.md",
    ]
    assert plan.documents[0].category == "stable"
    assert plan.stable_tokens > 0
    assert plan.dynamic_tokens > 0
    assert plan.within_budget
    assert len(plan.stable_fingerprint) == 64


def test_stable_fingerprint_ignores_dynamic_changes(tmp_path: Path) -> None:
    _repo(tmp_path)
    first = build_context_plan(tmp_path)
    task = tmp_path / "docs/tasks/T-1.md"
    task.write_text("# Task\nchanged dynamic content\n", encoding="utf-8")
    second = build_context_plan(tmp_path)
    assert first.stable_fingerprint == second.stable_fingerprint
    assert first.dynamic_fingerprint != second.dynamic_fingerprint


def test_context_plan_reports_budget_and_file_limits(tmp_path: Path) -> None:
    _repo(tmp_path)
    plan = build_context_plan(tmp_path, budget_tokens=1, max_files=2)
    assert not plan.ok
    assert not plan.within_budget
    assert any("configured maximum" in error for error in plan.errors)
''',
)

write(
    "tests/test_rotation_policy.py",
    '''from __future__ import annotations

from repo_state_agent.runtime.model import TokenUsage
from repo_state_agent.runtime.rotation import evaluate_rotation


def decide(input_tokens: int, cached: int, turns: int = 1):
    return evaluate_rotation(
        usage=TokenUsage(input_tokens=input_tokens, cached_input_tokens=cached),
        thread_turns=turns,
        max_turns_per_epoch=6,
        hard_input_tokens=60_000,
        soft_input_tokens=48_000,
        max_fresh_input_tokens=18_000,
        min_cache_reuse_ratio=0.5,
    )


def test_hard_and_turn_limits_rotate() -> None:
    assert decide(10_000, 8_000, turns=6).reason == "MAX_TURNS_PER_RUNTIME_EPOCH"
    assert decide(60_000, 55_000).reason == "HARD_INPUT_TOKEN_PRESSURE"


def test_fresh_input_pressure_rotates() -> None:
    decision = decide(40_000, 20_000)
    assert decision.rotate
    assert decision.reason == "FRESH_INPUT_TOKEN_PRESSURE"
    assert decision.fresh_input_tokens == 20_000


def test_soft_limit_uses_cache_quality() -> None:
    bad = decide(50_000, 20_000)
    good = decide(50_000, 40_000)
    assert bad.rotate and bad.reason == "FRESH_INPUT_TOKEN_PRESSURE"
    assert not good.rotate
    assert good.reason == "CACHE_LOCALITY_ACCEPTABLE"


def test_low_cache_reason_when_fresh_limit_is_disabled() -> None:
    decision = evaluate_rotation(
        usage=TokenUsage(input_tokens=50_000, cached_input_tokens=20_000),
        thread_turns=1,
        max_turns_per_epoch=6,
        hard_input_tokens=60_000,
        soft_input_tokens=48_000,
        max_fresh_input_tokens=0,
        min_cache_reuse_ratio=0.5,
    )
    assert decision.rotate
    assert decision.reason == "LOW_CACHE_REUSE_AT_SOFT_LIMIT"
''',
)

write(
    "tests/test_cli_context.py",
    '''from __future__ import annotations

import json
from pathlib import Path

from repo_state_agent.cli import main
from repo_state_agent.scaffold import initialize_repository


def test_context_command_reports_ordered_plan(tmp_path: Path, capsys) -> None:
    initialize_repository(tmp_path)
    assert main(["context", str(tmp_path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["documents"][0]["path"] == "AGENTS.md"
    assert payload["stable_tokens"] > 0
    assert payload["dynamic_tokens"] > 0
    assert payload["within_budget"] is True


def test_context_strict_fails_when_budget_is_exceeded(tmp_path: Path) -> None:
    initialize_repository(tmp_path)
    config = tmp_path / ".rsaw/config.json"
    raw = json.loads(config.read_text(encoding="utf-8"))
    raw["runtime"]["context"]["bootstrap_token_budget"] = 1
    config.write_text(json.dumps(raw), encoding="utf-8")
    assert main(["context", str(tmp_path), "--strict"]) == 1
''',
)

write(
    "tests/test_runtime_config.py",
    '''from __future__ import annotations

import json
from pathlib import Path

import pytest

from repo_state_agent.runtime.config import load_runtime_config


def test_runtime_config_defaults_without_file(tmp_path: Path) -> None:
    config = load_runtime_config(tmp_path)
    assert config.adapter == "codex"
    assert config.sandbox == "workspace-write"
    assert config.approve_for_me is False
    assert config.rotation_soft_input_tokens == 48_000
    assert config.bootstrap_token_budget == 15_000


def test_runtime_config_reads_legacy_limits(tmp_path: Path) -> None:
    (tmp_path / ".rsaw").mkdir()
    (tmp_path / ".rsaw/config.json").write_text(
        json.dumps({"runtime": {"max_turns_per_epoch": 3, "rotate_input_tokens": 40_000}}),
        encoding="utf-8",
    )
    config = load_runtime_config(tmp_path)
    assert config.max_turns_per_epoch == 3
    assert config.rotate_input_tokens == 40_000


def test_runtime_config_reads_nested_rotation_and_context(tmp_path: Path) -> None:
    (tmp_path / ".rsaw").mkdir()
    (tmp_path / ".rsaw/config.json").write_text(
        json.dumps(
            {
                "runtime": {
                    "rotation": {
                        "soft_input_tokens": 30_000,
                        "hard_input_tokens": 50_000,
                        "max_fresh_input_tokens": 12_000,
                        "min_cache_reuse_ratio": 0.7,
                    },
                    "context": {
                        "bootstrap_token_budget": 9_000,
                        "max_files": 8,
                        "enforce_budget": True,
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    config = load_runtime_config(tmp_path)
    assert config.rotation_soft_input_tokens == 30_000
    assert config.rotate_input_tokens == 50_000
    assert config.max_fresh_input_tokens == 12_000
    assert config.min_cache_reuse_ratio == 0.7
    assert config.bootstrap_token_budget == 9_000
    assert config.max_context_files == 8
    assert config.enforce_context_budget is True


def test_runtime_config_rejects_invalid_limit(tmp_path: Path) -> None:
    (tmp_path / ".rsaw").mkdir()
    (tmp_path / ".rsaw/config.json").write_text(
        json.dumps({"runtime": {"max_turns_per_epoch": 0}}), encoding="utf-8"
    )
    with pytest.raises(ValueError):
        load_runtime_config(tmp_path)


def test_runtime_config_rejects_soft_limit_above_hard_limit(tmp_path: Path) -> None:
    (tmp_path / ".rsaw").mkdir()
    (tmp_path / ".rsaw/config.json").write_text(
        json.dumps(
            {
                "runtime": {
                    "rotation": {
                        "soft_input_tokens": 70_000,
                        "hard_input_tokens": 60_000,
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_runtime_config(tmp_path)
''',
)

write(
    "tests/test_runtime_report.py",
    '''from __future__ import annotations

from repo_state_agent.runtime.report import efficiency_view


def test_efficiency_view_reports_context_cost_per_checkpoint() -> None:
    view = efficiency_view(
        {
            "run_id": "r1",
            "status": "COMPLETE",
            "reason": "WORKSTREAM_COMPLETE",
            "workstream": "W-1",
            "agent_turns": 4,
            "runtime_epochs": 2,
            "fresh_turns": 2,
            "resumed_turns": 2,
            "checkpoints_observed": 4,
            "transitions": {"CONTINUE": 2, "ROTATE": 2, "COMPLETE": 1},
            "total_usage": {
                "input_tokens": 1000,
                "cached_input_tokens": 600,
                "output_tokens": 100,
            },
        }
    )
    assert view["input_tokens_per_checkpoint"] == 250.0
    assert view["fresh_input_tokens"] == 400
    assert view["fresh_input_tokens_per_checkpoint"] == 100.0
    assert view["cache_reuse_ratio"] == 0.6
    assert view["context_efficiency"]["rotations"] == 2
    assert view["runtime_epochs"] == 2
''',
)

write(
    "tests/test_prompt_context_policy.py",
    '''from __future__ import annotations

from pathlib import Path

from repo_state_agent.prompts import render_prompt
from repo_state_agent.scaffold import initialize_repository


def test_fresh_prompt_orders_stable_before_dynamic_authority(tmp_path: Path) -> None:
    initialize_repository(tmp_path)
    prompt = render_prompt(tmp_path, mode="fresh")
    assert "Resume the active RSAW workstream" in prompt
    assert prompt.index("Stable prefix:") < prompt.index("Dynamic authority:")
    assert prompt.index("AGENTS.md") < prompt.index("ACTIVE.md")
    assert "Stable policy fingerprint:" in prompt
    assert "Estimated bootstrap:" in prompt


def test_continue_prompt_avoids_reloading_stable_prefix(tmp_path: Path) -> None:
    initialize_repository(tmp_path)
    prompt = render_prompt(tmp_path, mode="continue")
    assert "Continue the active RSAW context epoch" in prompt
    assert "Do not reread stable-prefix files" in prompt
    assert "Re-read dynamic authority in this order" in prompt
    assert "docs/tasks/T-000-bootstrap.md" in prompt
''',
)

print("RSAW 0.5 core files staged")
