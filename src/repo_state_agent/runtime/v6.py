from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from ..active_format import (
    active_budget_errors,
    canonicalize_active_text,
    replace_section as replace_active_section,
)
from ..model import ActiveState
from ..parsing import parse_active
from ..verify import verify_repository
from .adapter import AgentAdapter
from .model import AgentTurnResult, TokenUsage
from .store import RuntimeLock, RuntimeStore, atomic_write_json, utc_now
from .tool_budget import is_broad_discovery

SCHEMA_RESULT = "rsaw.checkpoint-result.v1"
SCHEMA_CHECKPOINT = "rsaw.checkpoint.v6"
SCHEMA_CAPSULE = "rsaw.semantic-capsule.v1"
SCHEMA_ENVELOPE = "rsaw.context-envelope.v1"
SCHEMA_EVIDENCE = "rsaw.evidence.v1"
SCHEMA_REVIEW = "rsaw.review-manifest.v1"
VALID_ACTIONS = {"CONTINUE", "COMPACT", "ROTATE", "PAUSE", "COMPLETE"}
EventSink = Any


@dataclass(frozen=True)
class V6Options:
    context_window_tokens: int = 128_000
    target_envelope_tokens: int = 6_000
    hard_envelope_tokens: int = 12_000
    max_exact_evidence_tokens: int = 7_000
    max_capsule_tokens: int = 2_500
    max_validation_tokens: int = 1_000
    compact_candidate_ratio: float = 0.75
    compact_required_ratio: float = 0.85
    hard_turn_ceiling: int = 8
    max_transitions: int = 100
    max_total_input_tokens: int = 5_000_000
    max_tool_calls_per_turn: int = 32
    max_tool_output_tokens: int = 50_000
    max_single_tool_output_tokens: int = 20_000
    max_broad_discovery_commands: int = 2
    enforce_tool_budget: bool = True
    quiet: bool = False
    dry_run: bool = False

    @classmethod
    def from_root(cls, root: Path, *, quiet: bool = False, dry_run: bool = False) -> V6Options:
        raw: dict[str, Any] = {}
        path = root / ".rsaw/config.json"
        if path.is_file():
            value = json.loads(path.read_text(encoding="utf-8"))
            raw = value if isinstance(value, dict) else {}
        runtime = raw.get("runtime", {}) if isinstance(raw, dict) else {}
        if not isinstance(runtime, dict):
            runtime = {}
        v6 = runtime.get("v6", {}) if isinstance(runtime.get("v6", {}), dict) else {}
        compiler = (
            v6.get("contextCompiler", {}) if isinstance(v6.get("contextCompiler", {}), dict) else {}
        )
        governor = v6.get("governor", {}) if isinstance(v6.get("governor", {}), dict) else {}
        tool_budget = (
            runtime.get("toolBudget", {}) if isinstance(runtime.get("toolBudget", {}), dict) else {}
        )
        return cls(
            context_window_tokens=_pos(v6.get("contextWindowTokens"), 128_000),
            target_envelope_tokens=_pos(compiler.get("targetEnvelopeTokens"), 6_000),
            hard_envelope_tokens=_pos(compiler.get("hardEnvelopeTokens"), 12_000),
            max_exact_evidence_tokens=_pos(compiler.get("maxExactEvidenceTokens"), 7_000),
            max_capsule_tokens=_pos(compiler.get("maxSemanticCapsuleTokens"), 2_500),
            max_validation_tokens=_pos(compiler.get("maxValidationSummaryTokens"), 1_000),
            compact_candidate_ratio=_ratio(governor.get("compactCandidateRatio"), 0.75),
            compact_required_ratio=_ratio(governor.get("compactRequiredRatio"), 0.85),
            hard_turn_ceiling=_pos(governor.get("hardTurnCeiling"), 8),
            max_transitions=_pos(runtime.get("max_transitions"), 100),
            max_total_input_tokens=_nonneg(runtime.get("max_total_input_tokens"), 5_000_000),
            max_tool_calls_per_turn=_pos(tool_budget.get("maxToolCallsPerTurn"), 32),
            max_tool_output_tokens=_pos(tool_budget.get("maxToolOutputTokens"), 50_000),
            max_single_tool_output_tokens=_pos(
                tool_budget.get("maxSingleToolOutputTokens"), 20_000
            ),
            max_broad_discovery_commands=_nonneg(tool_budget.get("maxBroadDiscoveryCommands"), 2),
            enforce_tool_budget=bool(tool_budget.get("enforce", True)),
            quiet=quiet,
            dry_run=dry_run,
        )


@dataclass(frozen=True)
class TaskRef:
    task_id: str
    spec: str
    role: str

    @classmethod
    def from_value(cls, value: Any, *, default_role: str = "Builder") -> TaskRef | None:
        if not isinstance(value, dict):
            return None
        task_id = _s(value.get("id") or value.get("taskId") or value.get("task_id"))
        spec = _s(value.get("spec") or value.get("taskSpec") or value.get("task_spec"))
        role = _s(value.get("role")) or default_role
        if not task_id or not spec:
            return None
        return cls(task_id, spec, role)


@dataclass(frozen=True)
class CheckpointResult:
    schema_version: str
    outcome: str
    summary: str
    changed_files: tuple[str, ...]
    validations: tuple[dict[str, Any], ...]
    artifacts: tuple[dict[str, Any], ...]
    capsule_delta: dict[str, Any]
    next_task: TaskRef | None
    following_task: TaskRef | None
    next_action: str
    stop_condition: str
    requested_action: str
    transition_reason: str
    human_gate: str

    @classmethod
    def parse(cls, text: str) -> CheckpointResult:
        payload = _extract_json(text)
        if payload.get("schemaVersion") != SCHEMA_RESULT:
            raise ValueError(f"checkpoint result must use {SCHEMA_RESULT}")
        action = _s(payload.get("requestedAction") or "CONTINUE").upper()
        if action not in VALID_ACTIONS:
            raise ValueError(f"invalid requestedAction: {action}")
        changed = payload.get("changedFiles", [])
        validations = payload.get("validations", [])
        artifacts = payload.get("artifacts", [])
        capsule_delta = payload.get("semanticCapsuleDelta", {})
        if not isinstance(changed, list) or not all(isinstance(x, str) for x in changed):
            raise ValueError("changedFiles must be a string list")
        if not isinstance(validations, list) or not all(isinstance(x, dict) for x in validations):
            raise ValueError("validations must be an object list")
        if not isinstance(artifacts, list) or not all(isinstance(x, dict) for x in artifacts):
            raise ValueError("artifacts must be an object list")
        if not isinstance(capsule_delta, dict):
            raise ValueError("semanticCapsuleDelta must be an object")
        return cls(
            schema_version=SCHEMA_RESULT,
            outcome=_s(payload.get("outcome") or "PASS").upper(),
            summary=_s(payload.get("summary")),
            changed_files=tuple(changed),
            validations=tuple(validations),
            artifacts=tuple(artifacts),
            capsule_delta=capsule_delta,
            next_task=TaskRef.from_value(payload.get("nextTask")),
            following_task=TaskRef.from_value(payload.get("followingTask")),
            next_action=_s(payload.get("nextAction")),
            stop_condition=_s(payload.get("stopCondition")),
            requested_action=action,
            transition_reason=_s(payload.get("transitionReason")),
            human_gate=_s(payload.get("humanGate")),
        )


@dataclass(frozen=True)
class EvidenceHandle:
    evidence_id: str
    kind: str
    sha256: str
    source: str
    bytes: int
    approx_tokens: int
    store_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SemanticCapsule:
    workstream_id: str
    checkpoint_id: str = ""
    source_revision: str = ""
    role: str = ""
    objective: str = ""
    observed_facts: list[dict[str, Any]] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    excluded_hypotheses: list[dict[str, Any]] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    unresolved_risks: list[dict[str, Any]] = field(default_factory=list)
    code_relations: list[dict[str, Any]] = field(default_factory=list)
    validation_status: list[dict[str, Any]] = field(default_factory=list)
    next_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": SCHEMA_CAPSULE,
            "workstreamId": self.workstream_id,
            "checkpointId": self.checkpoint_id,
            "sourceRevision": self.source_revision,
            "role": self.role,
            "objective": self.objective,
            "observedFacts": self.observed_facts,
            "decisions": self.decisions,
            "excludedHypotheses": self.excluded_hypotheses,
            "evidenceRefs": self.evidence_refs,
            "unresolvedRisks": self.unresolved_risks,
            "codeRelations": self.code_relations,
            "validationStatus": self.validation_status,
            "nextAction": self.next_action,
        }

    @classmethod
    def load(cls, root: Path, workstream_id: str) -> SemanticCapsule:
        path = root / ".rsaw/state/capsules" / f"{_safe_name(workstream_id or 'classic')}.json"
        if not path.is_file():
            return cls(workstream_id=workstream_id or "classic")
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or value.get("schemaVersion") != SCHEMA_CAPSULE:
            return cls(workstream_id=workstream_id or "classic")
        return cls(
            workstream_id=_s(value.get("workstreamId")) or workstream_id or "classic",
            checkpoint_id=_s(value.get("checkpointId")),
            source_revision=_s(value.get("sourceRevision")),
            role=_s(value.get("role")),
            objective=_s(value.get("objective")),
            observed_facts=_obj_list(value.get("observedFacts")),
            decisions=_obj_list(value.get("decisions")),
            excluded_hypotheses=_obj_list(value.get("excludedHypotheses")),
            evidence_refs=_str_list(value.get("evidenceRefs")),
            unresolved_risks=_obj_list(value.get("unresolvedRisks")),
            code_relations=_obj_list(value.get("codeRelations")),
            validation_status=_obj_list(value.get("validationStatus")),
            next_action=_s(value.get("nextAction")),
        )

    def merge(
        self,
        delta: dict[str, Any],
        *,
        checkpoint_id: str,
        revision: str,
        role: str,
        objective: str,
        evidence_refs: list[str],
        max_tokens: int,
    ) -> None:
        mapping = {
            "observedFacts": "observed_facts",
            "decisions": "decisions",
            "excludedHypotheses": "excluded_hypotheses",
            "unresolvedRisks": "unresolved_risks",
            "codeRelations": "code_relations",
            "validationStatus": "validation_status",
        }
        for external, internal in mapping.items():
            incoming = _obj_list(delta.get(external))
            setattr(self, internal, _merge_semantic(getattr(self, internal), incoming))
        # Authoritative evidence is bound by the supervisor after the turn.
        # Model-provided source labels are non-authoritative hints and are not persisted.
        incoming_refs = evidence_refs
        self.evidence_refs = list(dict.fromkeys([*self.evidence_refs, *incoming_refs]))[-64:]
        self.checkpoint_id = checkpoint_id
        self.source_revision = revision
        self.role = role
        self.objective = objective
        self.next_action = _s(delta.get("nextAction")) or self.next_action
        self._prune(max_tokens)

    def _prune(self, max_tokens: int) -> None:
        self.unresolved_risks = [x for x in self.unresolved_risks if not bool(x.get("resolved"))][
            -24:
        ]
        self.code_relations = self.code_relations[-24:]
        self.validation_status = self.validation_status[-24:]
        self.observed_facts = self.observed_facts[-48:]
        self.decisions = self.decisions[-32:]
        self.excluded_hypotheses = self.excluded_hypotheses[-32:]
        while _tokens(json.dumps(self.to_dict(), sort_keys=True)) > max_tokens:
            candidates = [
                self.code_relations,
                self.validation_status,
                self.excluded_hypotheses,
                self.observed_facts,
                self.decisions,
                self.unresolved_risks,
                self.evidence_refs,
            ]
            target = max(candidates, key=len)
            if not target:
                break
            del target[0]

    def save(self, root: Path) -> Path:
        path = root / ".rsaw/state/capsules" / f"{_safe_name(self.workstream_id)}.json"
        atomic_write_json(path, self.to_dict())
        return path


@dataclass(frozen=True)
class ContextEnvelope:
    mode: str
    role: str
    task_id: str
    components: tuple[dict[str, Any], ...]
    total_tokens: int
    exact_evidence_tokens: int
    capsule_tokens: int
    validation_tokens: int
    repeated_input_tokens: int
    evidence_resend_tokens: int
    sha256: str
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": SCHEMA_ENVELOPE,
            "mode": self.mode,
            "role": self.role,
            "taskId": self.task_id,
            "components": list(self.components),
            "totalTokens": self.total_tokens,
            "exactEvidenceTokens": self.exact_evidence_tokens,
            "semanticCapsuleTokens": self.capsule_tokens,
            "validationSummaryTokens": self.validation_tokens,
            "repeatedInputTokens": self.repeated_input_tokens,
            "evidenceResendTokens": self.evidence_resend_tokens,
            "envelopeSha256": self.sha256,
            "warnings": list(self.warnings),
        }

    def prompt_text(self) -> str:
        parts = []
        for component in self.components:
            content = _s(component.get("content"))
            if content:
                parts.append(f"### {component.get('name')}\n{content}")
            else:
                parts.append(
                    f"### {component.get('name')}\nReference: {component.get('reference')}"
                )
        return "\n\n".join(parts)


@dataclass(frozen=True)
class GovernorDecision:
    action: str
    reason: str
    occupancy_ratio: float
    occupancy_tokens: int
    source: str = "estimated"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GateDecision:
    accepted: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    changed_files: tuple[str, ...]
    executed_commands: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class V6Summary:
    run_id: str
    repository: str
    started_at: str
    status: str = "RUNNING"
    reason: str = ""
    workstream: str = ""
    final_task: str = ""
    runtime_epochs: int = 0
    agent_turns: int = 0
    fresh_contexts: int = 0
    resumed_turns: int = 0
    checkpoints_observed: int = 0
    model_calls: int = 0
    tool_calls: int = 0
    context_compactions: int = 0
    role_rotations: int = 0
    forced_rotations: int = 0
    repeated_input_tokens: int = 0
    evidence_resend_tokens: int = 0
    context_envelope_tokens: int = 0
    semantic_capsule_tokens: int = 0
    deterministic_operations: int = 0
    recovery_rediscovery_commands: int = 0
    tool_output_tokens: int = 0
    peak_tool_output_tokens: int = 0
    tool_budget_aborts: int = 0
    sandbox_resolutions: list[dict[str, Any]] = field(default_factory=list)
    occupancy_samples: list[float] = field(default_factory=list)
    total_usage: TokenUsage = TokenUsage()
    human_gate: str = ""
    ended_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "total_usage": self.total_usage.to_dict(),
            "mean_context_occupancy": (
                round(sum(self.occupancy_samples) / len(self.occupancy_samples), 6)
                if self.occupancy_samples
                else None
            ),
            "fresh_input_tokens": max(
                0,
                self.total_usage.input_tokens - self.total_usage.cached_input_tokens,
            ),
        }


@dataclass(frozen=True)
class V6SupervisorResult:
    status: str
    reason: str
    run_id: str
    summary_path: Path | None
    exit_code: int


def v6_enabled(root: Path) -> bool:
    path = root / ".rsaw/config.json"
    if not path.is_file():
        return False
    value = json.loads(path.read_text(encoding="utf-8"))
    runtime = value.get("runtime", {}) if isinstance(value, dict) else {}
    v6 = runtime.get("v6", {}) if isinstance(runtime, dict) else {}
    return bool(v6.get("enabled")) if isinstance(v6, dict) else False


def migrate_v6(root: Path, *, apply: bool = False) -> dict[str, Any]:
    root = root.resolve()
    config_path = root / ".rsaw/config.json"
    active_path = root / "ACTIVE.md"
    before_active = _sha_file(active_path) if active_path.is_file() else ""
    raw: dict[str, Any] = {}
    if config_path.is_file():
        value = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(".rsaw/config.json must be an object")
        raw = value
    runtime = raw.setdefault("runtime", {})
    if not isinstance(runtime, dict):
        raise ValueError("runtime must be an object")
    raw["schema_version"] = 3
    runtime.setdefault("max_transitions", 100)
    runtime.setdefault("max_total_input_tokens", 5_000_000)
    runtime["v6"] = {
        "enabled": True,
        "contextWindowTokens": 128000,
        "contextCompiler": {
            "targetEnvelopeTokens": 6000,
            "hardEnvelopeTokens": 12000,
            "maxExactEvidenceTokens": 7000,
            "maxSemanticCapsuleTokens": 2500,
            "maxValidationSummaryTokens": 1000,
            "useReadIfChanged": True,
            "useEvidenceHandles": True,
            "useDeltaContext": True,
        },
        "governor": {
            "compactCandidateRatio": 0.75,
            "compactRequiredRatio": 0.85,
            "hardTurnCeiling": 8,
            "useAggregateProviderInputAsOccupancy": False,
        },
        "bookkeeping": {
            "agentMayMutateActive": False,
            "agentMayRunAdvance": False,
            "supervisorOwnsTransition": True,
        },
    }
    plan = {
        "target": "0.6",
        "apply": apply,
        "config": str(config_path.relative_to(root)),
        "backup": ".rsaw/config.v05.backup.json",
        "activeSha256Before": before_active,
        "preservesActive": True,
        "preservesWorktreeOutsideRsawConfig": True,
        "v6Enabled": True,
    }
    if not apply:
        return plan
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if config_path.is_file():
        backup = root / ".rsaw/config.v05.backup.json"
        if not backup.exists():
            backup.write_bytes(config_path.read_bytes())
    atomic_write_json(config_path, raw)
    after_active = _sha_file(active_path) if active_path.is_file() else ""
    if before_active != after_active:
        raise RuntimeError("migration changed ACTIVE.md; refusing migration")
    plan["activeSha256After"] = after_active
    plan["status"] = "MIGRATED"
    return plan


def migrate_v7(root: Path, *, apply: bool = False) -> dict[str, Any]:
    root = root.resolve()
    config_path = root / ".rsaw/config.json"
    active_path = root / "ACTIVE.md"
    before_active = _sha_file(active_path) if active_path.is_file() else ""
    raw: dict[str, Any] = {}
    if config_path.is_file():
        value = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(".rsaw/config.json must be an object")
        raw = value
    runtime = raw.setdefault("runtime", {})
    if not isinstance(runtime, dict):
        raise ValueError("runtime must be an object")
    raw["schema_version"] = 4
    runtime.setdefault("max_transitions", 100)
    runtime.setdefault("max_total_input_tokens", 5_000_000)
    v6 = runtime.setdefault("v6", {})
    if not isinstance(v6, dict):
        raise ValueError("runtime.v6 must be an object")
    v6.setdefault("enabled", True)
    v6.setdefault("contextWindowTokens", 128_000)
    v6.setdefault(
        "contextCompiler",
        {
            "targetEnvelopeTokens": 6_000,
            "hardEnvelopeTokens": 12_000,
            "maxExactEvidenceTokens": 7_000,
            "maxSemanticCapsuleTokens": 2_500,
            "maxValidationSummaryTokens": 1_000,
            "useReadIfChanged": True,
            "useEvidenceHandles": True,
            "useDeltaContext": True,
        },
    )
    v6.setdefault(
        "governor",
        {
            "compactCandidateRatio": 0.75,
            "compactRequiredRatio": 0.85,
            "hardTurnCeiling": 8,
            "useAggregateProviderInputAsOccupancy": False,
        },
    )
    v6.setdefault(
        "bookkeeping",
        {
            "agentMayMutateActive": False,
            "agentMayRunAdvance": False,
            "supervisorOwnsTransition": True,
        },
    )
    runtime.setdefault(
        "codex",
        {
            "binary": runtime.get("codex_binary", "codex"),
            "defaultSandbox": runtime.get("sandbox", "workspace-write"),
            "taskSandboxOverrides": {},
        },
    )
    runtime.setdefault(
        "toolBudget",
        {
            "maxToolCallsPerTurn": 32,
            "maxToolOutputTokens": 50_000,
            "maxSingleToolOutputTokens": 20_000,
            "maxBroadDiscoveryCommands": 2,
            "enforce": True,
        },
    )
    plan = {
        "target": "0.7",
        "apply": apply,
        "config": str(config_path.relative_to(root)),
        "backup": ".rsaw/config.v06.backup.json",
        "activeSha256Before": before_active,
        "preservesActive": True,
        "v7Enabled": True,
    }
    if not apply:
        return plan
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if config_path.is_file():
        backup = root / ".rsaw/config.v06.backup.json"
        if not backup.exists():
            backup.write_bytes(config_path.read_bytes())
    atomic_write_json(config_path, raw)
    after_active = _sha_file(active_path) if active_path.is_file() else ""
    if before_active != after_active:
        raise RuntimeError("migration changed ACTIVE.md; refusing migration")
    plan["activeSha256After"] = after_active
    plan["status"] = "MIGRATED"
    return plan


def compile_context(
    root: Path,
    *,
    mode: str = "FRESH",
    options: V6Options | None = None,
    previous_envelope: dict[str, Any] | None = None,
) -> ContextEnvelope:
    root = root.resolve()
    options = options or V6Options.from_root(root)
    state = parse_active(root)
    role = state.current_role or state.next_role or "Builder"
    capsule = SemanticCapsule.load(root, state.workstream_id)
    task_text = _bounded_file(state.task_spec, options.hard_envelope_tokens * 4)
    stable_text = _bounded_file(root / "AGENTS.md", 28_000)
    exact_parts: list[str] = []
    evidence_tokens = 0
    task_rel = state.task_spec.relative_to(root).as_posix()
    for path in state.required_reads:
        try:
            rel = path.resolve().relative_to(root).as_posix()
        except ValueError:
            continue
        if rel in {"AGENTS.md", "ACTIVE.md", task_rel}:
            continue
        if not path.is_file():
            continue
        content = _bounded_file(path, options.max_exact_evidence_tokens * 4)
        tokens = _tokens(content)
        if evidence_tokens + tokens > options.max_exact_evidence_tokens:
            exact_parts.append(f"{rel}: evidence://file/{_sha_text(content)[:16]}")
            continue
        evidence_tokens += tokens
        exact_parts.append(f"FILE {rel}\n{content}")

    components: list[dict[str, Any]] = []
    normalized_mode = mode.upper()
    if normalized_mode not in {"FRESH", "CONTINUE", "COMPACT", "REVIEW", "RECOVERY"}:
        raise ValueError(f"invalid context mode: {mode}")
    if normalized_mode != "CONTINUE":
        components.append(_component("Stable governance", stable_text, "stable"))
    else:
        components.append(
            {
                "name": "Stable governance",
                "category": "stable-ref",
                "reference": f"sha256:{_sha_text(stable_text)}",
                "tokens": 0,
                "sha256": _sha_text(stable_text),
            }
        )
    components.append(_component("Task contract", task_text, "exact"))
    if (
        capsule.observed_facts
        or capsule.decisions
        or capsule.excluded_hypotheses
        or capsule.unresolved_risks
    ):
        cap_text = json.dumps(capsule.to_dict(), indent=2, sort_keys=True)
        components.append(_component("Semantic capsule", cap_text, "semantic"))
    if exact_parts:
        components.append(_component("Exact evidence", "\n\n".join(exact_parts), "exact-evidence"))
    active_digest = _sha_file(root / "ACTIVE.md")
    delta = {
        "activeTask": state.task_id,
        "nextAction": state.next_action,
        "stopCondition": state.stop_condition,
        "humanGate": state.human_gate or None,
        "activeDigest": active_digest,
    }
    components.append(_component("Current delta", json.dumps(delta, indent=2), "delta"))

    previous = previous_envelope or {}
    previous_digests = (
        {c.get("sha256") for c in previous.get("components", []) if isinstance(c, dict)}
        if isinstance(previous, dict)
        else set()
    )
    repeated = sum(
        int(c.get("tokens", 0))
        for c in components
        if c.get("sha256") in previous_digests and c.get("content")
    )
    resend = sum(
        int(c.get("tokens", 0))
        for c in components
        if c.get("category") == "exact-evidence" and c.get("sha256") in previous_digests
    )
    total = sum(int(c.get("tokens", 0)) for c in components)
    capsule_tokens = sum(
        int(c.get("tokens", 0)) for c in components if c.get("category") == "semantic"
    )
    warnings: list[str] = []
    if total > options.target_envelope_tokens:
        warnings.append(f"envelope exceeds target: {total}>{options.target_envelope_tokens}")
    if total > options.hard_envelope_tokens:
        raise ValueError(
            f"context envelope exceeds hard budget: {total}>{options.hard_envelope_tokens}"
        )
    payload = json.dumps(components, sort_keys=True, separators=(",", ":"))
    return ContextEnvelope(
        normalized_mode,
        role,
        state.task_id,
        tuple(components),
        total,
        evidence_tokens,
        capsule_tokens,
        0,
        repeated,
        resend,
        _sha_text(payload),
        tuple(warnings),
    )


def store_evidence(root: Path, *, kind: str, source: str, content: str) -> EvidenceHandle:
    digest = _sha_text(content)
    evidence_id = f"EV-{kind.upper()}-{digest[:16]}"
    path = root / ".rsaw/state/evidence" / f"{evidence_id}.json"
    if not path.exists():
        atomic_write_json(
            path,
            {
                "schemaVersion": SCHEMA_EVIDENCE,
                "evidenceId": evidence_id,
                "kind": kind,
                "source": source,
                "sha256": digest,
                "bytes": len(content.encode("utf-8")),
                "approxTokens": _tokens(content),
                "content": content,
            },
        )
    return EvidenceHandle(
        evidence_id,
        kind,
        digest,
        source,
        len(content.encode("utf-8")),
        _tokens(content),
        path.relative_to(root).as_posix(),
    )


def read_if_changed(root: Path, relative: str, known_sha256: str | None) -> dict[str, Any]:
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        raise ValueError("read-if-changed path escapes repository") from None
    if not path.is_file():
        return {"changed": True, "exists": False, "path": relative}
    digest = _sha_file(path)
    if known_sha256 and digest == known_sha256:
        return {
            "changed": False,
            "exists": True,
            "path": relative,
            "sha256": digest,
        }
    text = path.read_text(encoding="utf-8")
    return {
        "changed": True,
        "exists": True,
        "path": relative,
        "sha256": digest,
        "content": text,
        "approxTokens": _tokens(text),
    }


def governor_decision(
    *,
    current_role: str,
    next_role: str,
    requested_action: str,
    human_gate: str,
    complete: bool,
    estimated_occupancy_tokens: int,
    context_window_tokens: int,
    compact_candidate_ratio: float,
    compact_required_ratio: float,
    thread_turns: int,
    hard_turn_ceiling: int,
) -> GovernorDecision:
    ratio = estimated_occupancy_tokens / max(1, context_window_tokens)
    if human_gate or requested_action == "PAUSE":
        return GovernorDecision(
            "PAUSE",
            "HUMAN_GATE" if human_gate else "AGENT_REQUESTED_PAUSE",
            ratio,
            estimated_occupancy_tokens,
        )
    if complete or requested_action == "COMPLETE":
        return GovernorDecision(
            "COMPLETE", "WORKSTREAM_STOP_CONDITION", ratio, estimated_occupancy_tokens
        )
    if _role(current_role) != _role(next_role):
        return GovernorDecision("ROTATE", "ROLE_BOUNDARY", ratio, estimated_occupancy_tokens)
    if requested_action == "ROTATE":
        return GovernorDecision(
            "ROTATE", "AGENT_REQUESTED_ROTATE", ratio, estimated_occupancy_tokens
        )
    if requested_action == "COMPACT":
        return GovernorDecision(
            "COMPACT", "AGENT_REQUESTED_COMPACT", ratio, estimated_occupancy_tokens
        )
    if ratio >= compact_required_ratio:
        return GovernorDecision(
            "COMPACT", "CONTEXT_OCCUPANCY_REQUIRED", ratio, estimated_occupancy_tokens
        )
    if ratio >= compact_candidate_ratio or thread_turns >= hard_turn_ceiling:
        return GovernorDecision(
            "COMPACT",
            (
                "CONTEXT_OCCUPANCY_PRESSURE"
                if ratio >= compact_candidate_ratio
                else "HARD_TURN_CEILING"
            ),
            ratio,
            estimated_occupancy_tokens,
        )
    return GovernorDecision(
        "CONTINUE", "COHERENT_WORKING_CONTEXT", ratio, estimated_occupancy_tokens
    )


def inspect_turn_events(result: AgentTurnResult, root: Path) -> dict[str, Any]:
    tool_calls = 0
    command_records: dict[str, dict[str, Any]] = {}
    command_order: list[str] = []
    started: set[str] = set()
    completed_output: set[str] = set()
    broad_discovery: set[str] = set()
    retained_output_tokens = 0
    peak_tool_output_tokens = 0

    if result.events_path and result.events_path.is_file():
        for line in result.events_path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            item = event.get("item")
            payload = item if isinstance(item, dict) else event
            item_type = _s(payload.get("type")).lower()
            event_type = _s(event.get("type"))
            cmd = payload.get("command") or payload.get("cmd")
            if isinstance(cmd, list):
                cmd = " ".join(str(x) for x in cmd)
            command = _one_line(cmd) if isinstance(cmd, str) else ""
            identity = _s(payload.get("id") or event.get("id")) or command or item_type

            is_tool = item_type in {
                "command_execution",
                "command",
                "shell",
                "shell_command",
                "tool_call",
                "mcp_tool_call",
                "function_call",
            }
            if is_tool and event_type.endswith(".started") and identity not in started:
                started.add(identity)
                tool_calls += 1
                if command and is_broad_discovery(command):
                    broad_discovery.add(identity)

            if command and item_type in {
                "command_execution",
                "command",
                "shell",
                "shell_command",
            }:
                if identity not in command_records:
                    command_order.append(identity)
                record = command_records.get(identity, {"command": command})
                record["command"] = command
                record["eventType"] = event_type
                exit_code = _maybe_int(
                    payload.get("exit_code")
                    if payload.get("exit_code") is not None
                    else payload.get("exitCode")
                )
                if exit_code is not None or event_type.endswith(".completed"):
                    record["exitCode"] = exit_code
                command_records[identity] = record

            if is_tool and event_type.endswith(".completed") and identity not in completed_output:
                completed_output.add(identity)
                output = (
                    payload.get("aggregated_output")
                    or payload.get("output")
                    or payload.get("stdout")
                )
                if isinstance(output, str):
                    output_tokens = _tokens(output)
                    retained_output_tokens += output_tokens
                    peak_tool_output_tokens = max(peak_tool_output_tokens, output_tokens)

    commands = [command_records[key] for key in command_order]
    return {
        "tool_calls": tool_calls,
        "commands": commands,
        "retained_tool_output_tokens": retained_output_tokens,
        "peak_tool_output_tokens": peak_tool_output_tokens,
        "broad_discovery_commands": len(broad_discovery),
    }


def deterministic_gate(
    root: Path,
    *,
    state: ActiveState,
    result: CheckpointResult,
    active_sha_before: str,
    changed_files: tuple[str, ...],
    event_info: dict[str, Any],
    evidence_ids: set[str],
) -> GateDecision:
    errors: list[str] = []
    warnings: list[str] = []
    if _sha_file(root / "ACTIVE.md") != active_sha_before:
        errors.append("MODEL_MUTATED_ACTIVE")
    executed_records = [x for x in event_info.get("commands", []) if isinstance(x, dict)]
    executed = [_one_line(x.get("command")) for x in executed_records if x.get("command")]
    actual = {x for x in changed_files if not _excluded(x)}
    declared = set(result.changed_files)
    if actual != declared:
        missing = sorted(actual - declared)
        extra = sorted(declared - actual)
        if missing:
            errors.append("UNREPORTED_CHANGED_FILES:" + ",".join(missing))
        if extra:
            errors.append("DECLARED_BUT_UNCHANGED_FILES:" + ",".join(extra))
    contract = parse_task_contract(state.task_spec)
    allowed = contract.get("allowed_writes", [])
    if allowed:
        forbidden = [x for x in actual if not any(fnmatch(x, pattern) for pattern in allowed)]
        if forbidden:
            errors.append("FORBIDDEN_WRITES:" + ",".join(sorted(forbidden)))
    required_validations = contract.get("validations", [])
    for required in required_validations:
        matches = [
            record for record in executed_records if required in _one_line(record.get("command"))
        ]
        if not matches:
            errors.append("VALIDATION_NOT_EXECUTED:" + required)
            continue
        statuses = [record.get("exitCode") for record in matches]
        if any(status not in {None, 0} for status in statuses):
            errors.append("VALIDATION_FAILED:" + required)
        elif all(status is None for status in statuses):
            warnings.append(f"VALIDATION_COMPLETION_STATUS_UNAVAILABLE:{required}")
    for artifact in result.artifacts:
        path_value = _s(artifact.get("path"))
        if not path_value:
            errors.append("ARTIFACT_PATH_MISSING")
            continue
        path = (root / path_value).resolve()
        try:
            path.relative_to(root.resolve())
        except ValueError:
            errors.append(f"ARTIFACT_ESCAPES_REPOSITORY:{path_value}")
            continue
        if not path.is_file():
            errors.append(f"ARTIFACT_MISSING:{path_value}")
            continue
        expected = _s(artifact.get("sha256"))
        if expected and _sha_file(path) != expected:
            errors.append(f"ARTIFACT_CHECKSUM_MISMATCH:{path_value}")
    refs = set(_str_list(result.capsule_delta.get("evidenceRefs")))
    claimed_handles = {ref for ref in refs if ref.startswith("EV-")}
    unknown_handles = claimed_handles - evidence_ids
    if unknown_handles:
        errors.append("UNKNOWN_EVIDENCE_REFS:" + ",".join(sorted(unknown_handles)))
    if refs - claimed_handles:
        warnings.append("MODEL_SOURCE_REFS_IGNORED:SUPERVISOR_OWNS_EVIDENCE_BINDING")
    if result.requested_action != "COMPLETE":
        if result.next_task is None:
            errors.append("NEXT_TASK_REQUIRED")
        else:
            next_path = (root / result.next_task.spec).resolve()
            try:
                next_path.relative_to(root.resolve())
            except ValueError:
                errors.append("NEXT_TASK_ESCAPES_REPOSITORY")
            else:
                if not next_path.is_file():
                    errors.append(f"NEXT_TASK_NOT_READY:{result.next_task.spec}")
    if not contract.get("validations"):
        warnings.append("TASK_HAS_NO_STRUCTURED_VALIDATION_CONTRACT")
    return GateDecision(
        not errors,
        tuple(errors),
        tuple(warnings),
        tuple(sorted(actual)),
        tuple(executed),
    )


def parse_task_contract(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"allowed_writes": [], "validations": []}
    text = path.read_text(encoding="utf-8")
    return {
        "allowed_writes": _section_bullets(text, "Allowed Writes"),
        "validations": [_strip_ticks(x) for x in _section_bullets(text, "Validation")],
    }


def _resolve_adapter_turn_settings(
    adapter: AgentAdapter, environment: dict[str, str]
) -> dict[str, str]:
    resolver = getattr(adapter, "resolve_turn_settings", None)
    if not callable(resolver):
        return {}
    value = resolver(dict(environment))
    if not isinstance(value, dict):
        raise ValueError("adapter turn settings must be an object")
    task = _s(value.get("task")) or environment.get("RSAW_TASK_ID", "")
    sandbox = _s(value.get("sandbox"))
    source = _s(value.get("source")) or "adapter"
    if not sandbox:
        raise ValueError("adapter turn settings omitted sandbox")
    return {"task": task, "sandbox": sandbox, "source": source}


def supervise_v6(
    root: Path,
    adapter: AgentAdapter,
    options: V6Options,
    *,
    event_sink: EventSink | None = None,
) -> V6SupervisorResult:
    root = root.resolve()
    verification = verify_repository(root)
    if not verification.ok:
        return V6SupervisorResult("FAILED", "REPOSITORY_VERIFICATION_FAILED", "", None, 23)
    state = parse_active(root)
    run_id = f"rsaw-v7-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    store = RuntimeStore(root, run_id)
    summary = V6Summary(
        run_id=run_id,
        repository=str(root),
        started_at=utc_now(),
        workstream=state.workstream_id,
    )
    _save_v6_summary(store, summary)
    _emit(
        store,
        event_sink,
        {
            "type": "v6.supervisor.started",
            "run_id": run_id,
            "runtime": "v0.7.1",
            "workstream": state.workstream_id,
            "task": state.task_id,
        },
    )

    def finish(status: str, reason: str, code: int) -> V6SupervisorResult:
        current = _safe_state(root, state)
        summary.status = status
        summary.reason = reason
        summary.final_task = current.task_id
        summary.human_gate = current.human_gate
        summary.ended_at = utc_now()
        _save_v6_summary(store, summary)
        _emit(
            store,
            event_sink,
            {
                "type": "v6.supervisor.terminal",
                "runtime": "v0.7.1",
                "status": status,
                "reason": reason,
            },
        )
        return V6SupervisorResult(status, reason, run_id, store.summary_path, code)

    if state.human_gate:
        return finish("PAUSED", "HUMAN_GATE", 20)
    if options.dry_run:
        try:
            envelope = compile_context(root, mode="FRESH", options=options)
        except ValueError as exc:
            return finish("FAILED", f"CONTEXT_COMPILATION_FAILED:{exc}", 27)
        _emit(
            store,
            event_sink,
            {"type": "v6.context.compiled", **envelope.to_dict()},
        )
        return finish("DRY_RUN", "V7_READY", 0)

    doctor = adapter.doctor()
    if not doctor.ok:
        return finish("FAILED", "ADAPTER_DOCTOR_FAILED:" + ";".join(doctor.errors), 22)

    thread_id: str | None = None
    thread_turns = 0
    epoch_tokens_estimate = 0
    previous_envelope: dict[str, Any] | None = None
    next_mode = "FRESH"
    checkpoint_index = _next_checkpoint_index(root)

    try:
        with RuntimeLock.for_root(root):
            for _ in range(options.max_transitions):
                state = parse_active(root)
                if state.human_gate:
                    return finish("PAUSED", "HUMAN_GATE", 20)
                try:
                    envelope = compile_context(
                        root,
                        mode=next_mode,
                        options=options,
                        previous_envelope=previous_envelope,
                    )
                except ValueError as exc:
                    return finish("FAILED", f"CONTEXT_COMPILATION_FAILED:{exc}", 27)
                envelope_path = (
                    root
                    / ".rsaw/state/envelopes"
                    / run_id
                    / f"turn-{summary.agent_turns + 1:04d}.json"
                )
                atomic_write_json(envelope_path, envelope.to_dict())
                _emit(
                    store,
                    event_sink,
                    {"type": "v6.context.compiled", **envelope.to_dict()},
                )
                summary.context_envelope_tokens += envelope.total_tokens
                summary.repeated_input_tokens += envelope.repeated_input_tokens
                summary.evidence_resend_tokens += envelope.evidence_resend_tokens
                if thread_id is None:
                    summary.runtime_epochs += 1
                    summary.fresh_contexts += 1
                    thread_turns = 0
                    epoch_tokens_estimate = envelope.total_tokens
                else:
                    epoch_tokens_estimate += envelope.total_tokens
                summary.agent_turns += 1
                summary.model_calls += 1
                thread_turns += 1
                active_sha_before = _sha_file(root / "ACTIVE.md")
                dirty_before = _dirty_hashes(root)
                prompt = _v6_prompt(state, envelope)
                turn_environment = {
                    "RSAW_SUPERVISED": "1",
                    "RSAW_V6": "1",
                    "RSAW_V7": "1",
                    "RSAW_RUNTIME_VERSION": "0.7.1",
                    "RSAW_RUN_ID": run_id,
                    "RSAW_TASK_ID": state.task_id,
                    "RSAW_ROLE": state.current_role or state.next_role,
                }
                try:
                    turn_settings = _resolve_adapter_turn_settings(adapter, turn_environment)
                except (TypeError, ValueError) as exc:
                    return finish("FAILED", f"SANDBOX_RESOLUTION_FAILED:{exc}", 22)
                if turn_settings:
                    turn_environment["RSAW_RESOLVED_SANDBOX"] = turn_settings["sandbox"]
                    turn_environment["RSAW_SANDBOX_SOURCE"] = turn_settings["source"]
                    resolution = {
                        "turn": summary.agent_turns,
                        "task": turn_settings["task"],
                        "sandbox": turn_settings["sandbox"],
                        "source": turn_settings["source"],
                    }
                    summary.sandbox_resolutions.append(resolution)
                    _emit(
                        store,
                        event_sink,
                        {"type": "v7.sandbox.resolved", "runtime": "v0.7.1", **resolution},
                    )
                _emit(
                    store,
                    event_sink,
                    {
                        "type": "v6.agent.turn.started",
                        "runtime": "v0.7.1",
                        "turn": summary.agent_turns,
                        "mode": next_mode,
                        "task": state.task_id,
                        "role": state.current_role,
                        "sandbox": turn_settings.get("sandbox"),
                        "sandboxSource": turn_settings.get("source"),
                    },
                )
                turn = adapter.run_turn(
                    prompt=prompt,
                    root=root,
                    run_dir=store.run_dir,
                    turn_index=summary.agent_turns,
                    thread_id=thread_id,
                    environment=turn_environment,
                )
                summary.total_usage = summary.total_usage + turn.usage
                event_info = inspect_turn_events(turn, root)
                summary.tool_calls += int(event_info["tool_calls"])
                summary.tool_output_tokens += int(event_info["retained_tool_output_tokens"])
                summary.peak_tool_output_tokens = max(
                    summary.peak_tool_output_tokens,
                    int(event_info["peak_tool_output_tokens"]),
                )
                summary.recovery_rediscovery_commands += int(event_info["broad_discovery_commands"])
                epoch_tokens_estimate += turn.latest_turn_usage.output_tokens + int(
                    event_info["retained_tool_output_tokens"]
                )
                if not turn.ok:
                    if turn.error.startswith("TOOL_BUDGET_EXCEEDED:"):
                        summary.tool_budget_aborts += 1
                        return finish("PAUSED", turn.error, 26)
                    return finish(
                        "FAILED",
                        f"AGENT_TURN_FAILED:{turn.error or turn.exit_code}",
                        22,
                    )
                try:
                    result = CheckpointResult.parse(turn.last_message)
                except ValueError as exc:
                    return finish("FAILED", f"CHECKPOINT_RESULT_INVALID:{exc}", 28)
                dirty_after = _dirty_hashes(root)
                changed = tuple(
                    sorted(
                        path
                        for path in set(dirty_before) | set(dirty_after)
                        if dirty_before.get(path) != dirty_after.get(path) and not _excluded(path)
                    )
                )

                evidence_handles: list[EvidenceHandle] = []
                for path in changed:
                    file_path = root / path
                    if file_path.is_file() and file_path.stat().st_size <= 128_000:
                        content = file_path.read_text(encoding="utf-8", errors="replace")
                        evidence_handles.append(
                            store_evidence(
                                root,
                                kind="file",
                                source=path,
                                content=content,
                            )
                        )
                command_summary = json.dumps(event_info.get("commands", []), indent=2)
                if command_summary != "[]":
                    evidence_handles.append(
                        store_evidence(
                            root,
                            kind="validation",
                            source=f"turn-{summary.agent_turns}",
                            content=command_summary,
                        )
                    )
                evidence_ids = {handle.evidence_id for handle in evidence_handles}
                gate = deterministic_gate(
                    root,
                    state=state,
                    result=result,
                    active_sha_before=active_sha_before,
                    changed_files=changed,
                    event_info=event_info,
                    evidence_ids=evidence_ids,
                )
                _emit(
                    store,
                    event_sink,
                    {"type": "v6.gate", **gate.to_dict()},
                )
                if not gate.accepted:
                    return finish(
                        "FAILED",
                        "DETERMINISTIC_GATE_REJECTED:" + ";".join(gate.errors),
                        29,
                    )

                candidate_index = checkpoint_index + 1
                checkpoint_id = f"CP-{candidate_index:04d}"
                revision = _git_revision(root)
                capsule = SemanticCapsule.load(root, state.workstream_id)
                capsule.merge(
                    result.capsule_delta,
                    checkpoint_id=checkpoint_id,
                    revision=revision,
                    role=state.current_role or state.next_role,
                    objective=result.summary or state.next_action,
                    evidence_refs=[h.evidence_id for h in evidence_handles],
                    max_tokens=options.max_capsule_tokens,
                )
                complete = result.requested_action == "COMPLETE"
                next_role = (
                    result.next_task.role
                    if result.next_task
                    else (state.next_role or state.current_role)
                )
                decision = governor_decision(
                    current_role=state.current_role or state.next_role,
                    next_role=next_role,
                    requested_action=result.requested_action,
                    human_gate=result.human_gate,
                    complete=complete,
                    estimated_occupancy_tokens=epoch_tokens_estimate,
                    context_window_tokens=options.context_window_tokens,
                    compact_candidate_ratio=options.compact_candidate_ratio,
                    compact_required_ratio=options.compact_required_ratio,
                    thread_turns=thread_turns,
                    hard_turn_ceiling=options.hard_turn_ceiling,
                )
                next_task_id = result.next_task.task_id if result.next_task else state.task_id
                next_environment = {
                    "RSAW_TASK_ID": next_task_id,
                    "RSAW_ROLE": next_role,
                }
                try:
                    next_turn_settings = _resolve_adapter_turn_settings(adapter, next_environment)
                except (TypeError, ValueError) as exc:
                    return finish("FAILED", f"NEXT_SANDBOX_RESOLUTION_FAILED:{exc}", 22)
                if (
                    turn_settings
                    and next_turn_settings
                    and turn_settings["sandbox"] != next_turn_settings["sandbox"]
                    and decision.action in {"CONTINUE", "COMPACT"}
                ):
                    decision = GovernorDecision(
                        "ROTATE",
                        "SANDBOX_BOUNDARY",
                        decision.occupancy_ratio,
                        decision.occupancy_tokens,
                        source="sandbox-policy",
                    )
                    summary.forced_rotations += 1
                    _emit(
                        store,
                        event_sink,
                        {
                            "type": "v7.sandbox.boundary",
                            "runtime": "v0.7.1",
                            "fromTask": state.task_id,
                            "fromSandbox": turn_settings["sandbox"],
                            "toTask": next_task_id,
                            "toSandbox": next_turn_settings["sandbox"],
                        },
                    )
                summary.occupancy_samples.append(decision.occupancy_ratio)
                if decision.action == "COMPACT":
                    summary.context_compactions += 1
                elif decision.action == "ROTATE":
                    summary.role_rotations += 1
                _emit(
                    store,
                    event_sink,
                    {"type": "v6.governor", **decision.to_dict()},
                )

                proposed_active = _render_active_markdown(
                    root, state, result, decision, checkpoint_id
                )
                budget_errors = active_budget_errors(proposed_active)
                if budget_errors:
                    return finish(
                        "FAILED",
                        "PROPOSED_ACTIVE_INVALID:" + ";".join(budget_errors),
                        29,
                    )

                capsule_path = (
                    root / ".rsaw/state/capsules" / f"{_safe_name(capsule.workstream_id)}.json"
                )
                review_manifest_path = None
                if decision.action == "ROTATE" and _role(next_role) == "reviewer":
                    review_manifest_path = root / ".rsaw/state/reviews" / f"{checkpoint_id}.json"
                checkpoint_path = root / ".rsaw/state/checkpoints" / f"{checkpoint_id}.json"
                sidecar_path = checkpoint_path.with_suffix(checkpoint_path.suffix + ".sha256")
                if checkpoint_path.exists() or sidecar_path.exists():
                    return finish("FAILED", f"CHECKPOINT_ALREADY_EXISTS:{checkpoint_id}", 29)

                authority_paths = [
                    root / "ACTIVE.md",
                    root / ".rsaw/state/active.json",
                    capsule_path,
                ]
                if review_manifest_path is not None:
                    authority_paths.append(review_manifest_path)
                snapshots = {path: _snapshot_file(path) for path in authority_paths}

                try:
                    capsule_path = capsule.save(root)
                    summary.semantic_capsule_tokens += _tokens(
                        json.dumps(capsule.to_dict(), sort_keys=True)
                    )
                    if review_manifest_path is not None:
                        review_manifest_path = _write_review_manifest(
                            root,
                            checkpoint_id,
                            state,
                            result,
                            evidence_handles,
                            revision,
                        )
                    checkpoint = {
                        "schemaVersion": SCHEMA_CHECKPOINT,
                        "checkpointId": checkpoint_id,
                        "runId": run_id,
                        "workstreamId": state.workstream_id,
                        "taskId": state.task_id,
                        "sourceRevision": revision,
                        "acceptedAt": utc_now(),
                        "result": _checkpoint_result_dict(result),
                        "gate": gate.to_dict(),
                        "governor": decision.to_dict(),
                        "contextEnvelopeRef": envelope_path.relative_to(root).as_posix(),
                        "contextEnvelopeSha256": envelope.sha256,
                        "semanticCapsuleRef": capsule_path.relative_to(root).as_posix(),
                        "semanticCapsuleSha256": _sha_file(capsule_path),
                        "evidence": [h.to_dict() for h in evidence_handles],
                        "reviewManifestRef": (
                            review_manifest_path.relative_to(root).as_posix()
                            if review_manifest_path
                            else None
                        ),
                    }
                    atomic_write_json(checkpoint_path, checkpoint)
                    _write_sha_sidecar(checkpoint_path)
                    _write_active_pointer(
                        root,
                        state,
                        result,
                        decision,
                        checkpoint_id,
                        capsule_path,
                        revision,
                    )
                    (root / "ACTIVE.md").write_text(proposed_active, encoding="utf-8")
                    post = verify_repository(root)
                    if not post.ok:
                        raise RuntimeError(
                            "POST_ADVANCE_REPOSITORY_INVALID:" + ";".join(post.errors)
                        )
                except Exception as exc:
                    checkpoint_path.unlink(missing_ok=True)
                    sidecar_path.unlink(missing_ok=True)
                    for authority_path, snapshot in snapshots.items():
                        _restore_file(authority_path, snapshot)
                    return finish("FAILED", str(exc), 23)

                checkpoint_index = candidate_index
                summary.deterministic_operations += 5
                summary.checkpoints_observed += 1
                _emit(
                    store,
                    event_sink,
                    {
                        "type": "v6.checkpoint.sealed",
                        "checkpoint": checkpoint_id,
                        "task": state.task_id,
                        "nextAction": decision.action,
                    },
                )
                _save_v6_summary(store, summary)

                if (
                    options.max_total_input_tokens
                    and summary.total_usage.input_tokens >= options.max_total_input_tokens
                ):
                    return finish("LIMIT_REACHED", "MAX_TOTAL_INPUT_TOKENS", 24)
                if decision.action == "COMPLETE":
                    return finish("COMPLETE", decision.reason, 0)
                if decision.action == "PAUSE":
                    return finish("PAUSED", decision.reason, 20)
                if decision.action == "ROTATE":
                    thread_id = None
                    previous_envelope = None
                    next_mode = "REVIEW" if _role(next_role) == "reviewer" else "FRESH"
                elif decision.action == "COMPACT":
                    thread_id = None
                    previous_envelope = envelope.to_dict()
                    next_mode = "COMPACT"
                else:
                    thread_id = turn.thread_id
                    previous_envelope = envelope.to_dict()
                    next_mode = "CONTINUE"
                    summary.resumed_turns += 1
            return finish("LIMIT_REACHED", "MAX_TRANSITIONS", 25)
    except RuntimeError as exc:
        return finish("FAILED", f"RUNTIME_LOCK_ERROR:{exc}", 21)


def v6_efficiency_view(summary: dict[str, Any]) -> dict[str, Any]:
    checkpoints = int(summary.get("checkpoints_observed") or 0)
    usage = summary.get("total_usage") if isinstance(summary.get("total_usage"), dict) else {}
    total = int(usage.get("input_tokens") or 0)
    cached = min(total, int(usage.get("cached_input_tokens") or 0))
    fresh = max(0, total - cached)
    output = int(usage.get("output_tokens") or 0)
    payload = dict(summary)
    payload.update(
        {
            "fresh_input_tokens": fresh,
            "cache_reuse_ratio": (cached / total if total else None),
            "input_tokens_per_successful_checkpoint": (
                total / checkpoints if checkpoints else None
            ),
            "cached_input_tokens_per_successful_checkpoint": (
                cached / checkpoints if checkpoints else None
            ),
            "fresh_input_tokens_per_successful_checkpoint": (
                fresh / checkpoints if checkpoints else None
            ),
            "output_tokens_per_successful_checkpoint": (
                output / checkpoints if checkpoints else None
            ),
            "model_calls_per_successful_checkpoint": (
                int(summary.get("model_calls") or 0) / checkpoints if checkpoints else None
            ),
            "tool_calls_per_successful_checkpoint": (
                int(summary.get("tool_calls") or 0) / checkpoints if checkpoints else None
            ),
        }
    )
    return payload


def synthetic_acceptance(root: Path, horizon: int) -> dict[str, Any]:
    options = V6Options.from_root(root)
    actions: list[str] = []
    phases = ("Explore", "Plan", "Implement", "Review")
    roles = {
        "Explore": "Builder",
        "Plan": "Builder",
        "Implement": "Builder",
        "Review": "Reviewer",
    }
    current_role = roles[phases[0]]
    for index in range(1, horizon + 1):
        final = index == horizon
        next_phase = phases[index % len(phases)]
        next_role = current_role if final else roles[next_phase]
        requested = "COMPLETE" if final else "CONTINUE"
        turns_in_role = 1 + sum(1 for previous in actions[-2:] if previous == "CONTINUE")
        simulated_ratio = 0.80 if horizon >= 16 and index % 5 == 0 else 0.35
        decision = governor_decision(
            current_role=current_role,
            next_role=next_role,
            requested_action=requested,
            human_gate="",
            complete=final,
            estimated_occupancy_tokens=int(options.context_window_tokens * simulated_ratio),
            context_window_tokens=options.context_window_tokens,
            compact_candidate_ratio=options.compact_candidate_ratio,
            compact_required_ratio=options.compact_required_ratio,
            thread_turns=turns_in_role,
            hard_turn_ceiling=options.hard_turn_ceiling,
        )
        actions.append(decision.action)
        if decision.action == "ROTATE":
            current_role = next_role
    return {
        "schemaVersion": "rsaw.v6.acceptance.v1",
        "checkpoints": horizon,
        "continues": actions.count("CONTINUE"),
        "compactions": actions.count("COMPACT"),
        "rotations": actions.count("ROTATE"),
        "pauses": actions.count("PAUSE"),
        "completes": actions.count("COMPLETE"),
        "manualRelay": 0,
        "aggregateInputUsedAsOccupancy": False,
        "pass": (
            actions.count("COMPLETE") == 1
            and actions.count("PAUSE") == 0
            and actions.count("ROTATE") >= 1
            and (horizon < 16 or actions.count("COMPACT") >= 1)
        ),
    }


def _v6_prompt(state: ActiveState, envelope: ContextEnvelope) -> str:
    return f"""RSAW v0.7 SUPERVISED CHECKPOINT

Repository state is authoritative. The supervisor owns ACTIVE.md, checkpoint numbering,
state advancement, evidence binding, checksums, and lifecycle decisions.

HARD RULES
- Do NOT edit ACTIVE.md.
- Do NOT run advance.py or any RSAW state-advancement command.
- Do semantic engineering work for exactly the active task.
- Treat the compiled context below as the default working set.
- Do NOT run broad repository discovery (`rg --files`, `find .`, `tree`, or equivalent)
  unless a specific unresolved question cannot be answered from the envelope.
- Do NOT concatenate multiple long files into one command.
- Keep each tool result bounded. Prefer exact paths, line ranges, counts, hashes, and concise
  summaries; redirect verbose output to an artifact rather than returning it into context.
- Do not re-read unchanged files or ACTIVE.md unless resolving a concrete contradiction.
- Run task-relevant validation.
- Do not expose hidden chain-of-thought.
- semanticCapsuleDelta.evidenceRefs MUST be [] because the supervisor binds authoritative
  evidence handles after the turn.
- Use canonical nextTask keys: id, spec, role.
- Your FINAL MESSAGE must be exactly one JSON object matching rsaw.checkpoint-result.v1.

ACTIVE TASK: {state.task_id}
ROLE: {state.current_role or state.next_role}
CONTEXT MODE: {envelope.mode}
ENVELOPE SHA256: {envelope.sha256}

{envelope.prompt_text()}

FINAL JSON CONTRACT
{{
  "schemaVersion": "rsaw.checkpoint-result.v1",
  "outcome": "PASS|BLOCKED|COMPLETE",
  "summary": "concise factual checkpoint result",
  "changedFiles": ["path"],
  "validations": [{{"command": "...", "status": "PASS|FAIL"}}],
  "artifacts": [{{"path": "...", "sha256": "optional"}}],
  "semanticCapsuleDelta": {{"observedFacts": [], "decisions": [], "excludedHypotheses": [], "evidenceRefs": [], "unresolvedRisks": [], "codeRelations": [], "validationStatus": [], "nextAction": "..."}},
  "nextTask": {{"id": "T-next", "spec": "docs/tasks/T-next.md", "role": "Builder"}},
  "followingTask": null,
  "nextAction": "...",
  "stopCondition": "...",
  "requestedAction": "CONTINUE|COMPACT|ROTATE|PAUSE|COMPLETE",
  "transitionReason": "...",
  "humanGate": ""
}}
"""


def _write_review_manifest(
    root: Path,
    checkpoint_id: str,
    state: ActiveState,
    result: CheckpointResult,
    evidence_handles: list[EvidenceHandle],
    revision: str,
) -> Path:
    path = root / ".rsaw/state/reviews" / f"{checkpoint_id}.json"
    atomic_write_json(
        path,
        {
            "schemaVersion": SCHEMA_REVIEW,
            "checkpointId": checkpoint_id,
            "sourceRevision": revision,
            "claim": result.summary,
            "taskId": state.task_id,
            "acceptanceCriteria": parse_task_contract(state.task_spec),
            "changedFiles": list(result.changed_files),
            "validations": list(result.validations),
            "artifacts": list(result.artifacts),
            "knownRisks": _obj_list(result.capsule_delta.get("unresolvedRisks")),
            "evidenceHandles": [h.evidence_id for h in evidence_handles],
            "scope": "BOUNDED_REVIEW",
            "builderReasoningHistoryIncluded": False,
        },
    )
    return path


def _write_active_pointer(
    root: Path,
    state: ActiveState,
    result: CheckpointResult,
    decision: GovernorDecision,
    checkpoint_id: str,
    capsule_path: Path,
    revision: str,
) -> None:
    next_task = result.next_task
    atomic_write_json(
        root / ".rsaw/state/active.json",
        {
            "schemaVersion": "rsaw.active-pointer.v1",
            "checkpointId": checkpoint_id,
            "workstreamId": state.workstream_id,
            "taskId": (
                next_task.task_id if next_task and decision.action != "COMPLETE" else state.task_id
            ),
            "taskSpec": (
                next_task.spec
                if next_task and decision.action != "COMPLETE"
                else state.task_spec.relative_to(root).as_posix()
            ),
            "role": (
                next_task.role
                if next_task and decision.action != "COMPLETE"
                else state.current_role
            ),
            "lifecycleAction": decision.action,
            "sourceRevision": revision,
            "capsuleRef": capsule_path.relative_to(root).as_posix(),
            "updatedAt": utc_now(),
        },
    )


def _render_active_markdown(
    root: Path,
    state: ActiveState,
    result: CheckpointResult,
    decision: GovernorDecision,
    checkpoint_id: str,
) -> str:
    text = (root / "ACTIVE.md").read_text(encoding="utf-8")
    next_task = result.next_task
    if decision.action == "COMPLETE":
        continuation = "COMPLETE"
        active_id = state.task_id
        active_spec = state.task_spec.relative_to(root).as_posix()
        role = state.current_role or state.next_role
    else:
        assert next_task is not None
        active_id, active_spec, role = next_task.task_id, next_task.spec, next_task.role
        continuation = (
            "ROTATE_REQUIRED"
            if decision.action == "ROTATE"
            else ("STOP_REQUIRED" if decision.action == "PAUSE" else "CONTINUE_ALLOWED")
        )
    following = result.following_task
    text = _replace_section(text, "Context Epoch", f"ID: {state.epoch_id or 'E-v7'}\nRole: {role}")
    text = _replace_section(text, "Active Task", f"ID: {active_id}\nSpec: {active_spec}")
    text = _replace_section(
        text,
        "Required Reads",
        f"- AGENTS.md\n- ACTIVE.md\n- {active_spec}",
    )
    text = _replace_section(text, "Human Gate", result.human_gate or "None.")
    text = _replace_section(
        text,
        "Next Exact Action",
        result.next_action or "Continue from the sealed checkpoint.",
    )
    text = _replace_section(
        text,
        "Stop Condition",
        result.stop_condition or "Task acceptance criteria are satisfied.",
    )
    text = _replace_section(
        text,
        "Continuation Gate",
        f"Decision: {continuation}\nReason: {decision.action}:{decision.reason}; checkpoint={checkpoint_id}",
    )
    if following:
        text = _replace_section(
            text,
            "Next Task",
            f"ID: {following.task_id}\nSpec: {following.spec}",
        )
        text = _replace_section(text, "Next Session Role", following.role)
    elif next_task and decision.action != "COMPLETE":
        text = _replace_section(
            text,
            "Next Task",
            f"ID: {next_task.task_id}\nSpec: {next_task.spec}",
        )
        text = _replace_section(text, "Next Session Role", next_task.role)
    return canonicalize_active_text(text)


def _update_active_markdown(
    root: Path,
    state: ActiveState,
    result: CheckpointResult,
    decision: GovernorDecision,
    checkpoint_id: str,
) -> None:
    (root / "ACTIVE.md").write_text(
        _render_active_markdown(root, state, result, decision, checkpoint_id),
        encoding="utf-8",
    )


def _checkpoint_result_dict(result: CheckpointResult) -> dict[str, Any]:
    return {
        "schemaVersion": result.schema_version,
        "outcome": result.outcome,
        "summary": result.summary,
        "changedFiles": list(result.changed_files),
        "validations": list(result.validations),
        "artifacts": list(result.artifacts),
        "semanticCapsuleDelta": result.capsule_delta,
        "nextTask": asdict(result.next_task) if result.next_task else None,
        "followingTask": asdict(result.following_task) if result.following_task else None,
        "nextAction": result.next_action,
        "stopCondition": result.stop_condition,
        "requestedAction": result.requested_action,
        "transitionReason": result.transition_reason,
        "humanGate": result.human_gate,
    }


def _next_checkpoint_index(root: Path) -> int:
    maximum = 0
    directory = root / ".rsaw/state/checkpoints"
    if not directory.is_dir():
        return 0
    for path in directory.glob("CP-*.json"):
        match = re.fullmatch(r"CP-(\d+)\.json", path.name)
        if match:
            maximum = max(maximum, int(match.group(1)))
    return maximum


def _safe_state(root: Path, fallback: ActiveState) -> ActiveState:
    try:
        return parse_active(root)
    except Exception:
        return fallback


def _save_v6_summary(store: RuntimeStore, summary: V6Summary) -> None:
    atomic_write_json(store.summary_path, summary.to_dict())
    atomic_write_json(
        store.latest_path,
        {"run_id": summary.run_id, "summary": str(store.summary_path.relative_to(store.root))},
    )


def _emit(store: RuntimeStore, sink: EventSink | None, event: dict[str, Any]) -> None:
    payload = {**event, "timestamp": utc_now()}
    with (store.run_dir / "supervisor-events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    if sink is not None:
        try:
            sink(payload)
        except Exception:
            pass


def _dirty_hashes(root: Path) -> dict[str, str]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError("git status failed")
    paths: set[str] = set()
    items = result.stdout.split(b"\0")
    index = 0
    while index < len(items):
        item = items[index]
        index += 1
        if not item:
            continue
        text = item.decode("utf-8", errors="replace")
        status = text[:2]
        path = text[3:]
        if status[0] in {"R", "C"} and index < len(items):
            path = items[index].decode("utf-8", errors="replace")
            index += 1
        if path:
            paths.add(path)
    hashes: dict[str, str] = {}
    for path in paths:
        full = root / path
        hashes[path] = _sha_file(full) if full.is_file() else "<missing>"
    return hashes


def _excluded(path: str) -> bool:
    return path.startswith(".rsaw/runtime/") or path.startswith(".rsaw/state/")


def _git_revision(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "UNAVAILABLE"


def _task_identity(state: ActiveState) -> str:
    return f"{state.task_id}|{state.task_spec}"


def _checkpoint_result_dict_for_hash(result: CheckpointResult) -> str:
    return json.dumps(_checkpoint_result_dict(result), sort_keys=True, separators=(",", ":"))


def _write_sha_sidecar(path: Path) -> None:
    path.with_suffix(path.suffix + ".sha256").write_text(
        f"{_sha_file(path)}  {path.name}\n", encoding="utf-8"
    )


def _snapshot_file(path: Path) -> bytes | None:
    return path.read_bytes() if path.is_file() else None


def _restore_file(path: Path, snapshot: bytes | None) -> None:
    if snapshot is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(snapshot)


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        value = json.loads(text)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        value = json.loads(fenced.group(1))
        if isinstance(value, dict):
            return value
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        value = json.loads(text[start : end + 1])
        if isinstance(value, dict):
            return value
    raise ValueError("final message does not contain a JSON object")


def _section_bullets(text: str, heading: str) -> list[str]:
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)",
        text,
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    if not match:
        return []
    values = []
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            values.append(stripped[2:].strip())
    return values


def _replace_section(text: str, heading: str, body: str) -> str:
    return replace_active_section(text, heading, body)


def _component(name: str, content: str, category: str) -> dict[str, Any]:
    return {
        "name": name,
        "category": category,
        "content": content,
        "tokens": _tokens(content),
        "sha256": _sha_text(content),
    }


def _bounded_file(path: Path, max_bytes: int) -> str:
    data = path.read_bytes()
    if len(data) > max_bytes:
        raise ValueError(f"context source exceeds byte limit: {path} ({len(data)}>{max_bytes})")
    return data.decode("utf-8")


def _merge_semantic(
    existing: list[dict[str, Any]], incoming: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for index, item in enumerate([*existing, *incoming]):
        identity = _s(item.get("id")) or f"anon:{_sha_text(json.dumps(item, sort_keys=True))[:16]}"
        if identity not in merged:
            order.append(identity)
        merged[identity] = {**item, "_order": index}
    return [
        {key: value for key, value in merged[item].items() if key != "_order"} for item in order
    ]


def _role(value: str) -> str:
    return _s(value).lower().replace("_", "-")


def _tokens(value: str) -> int:
    return (len(value) + 3) // 4


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ""


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value or "classic").strip("-") or "classic"


def _s(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _str_list(value: Any) -> list[str]:
    return [x for x in value if isinstance(x, str) and x.strip()] if isinstance(value, list) else []


def _obj_list(value: Any) -> list[dict[str, Any]]:
    return [dict(x) for x in value if isinstance(x, dict)] if isinstance(value, list) else []


def _one_line(value: Any) -> str:
    return " ".join(value.split()) if isinstance(value, str) else ""


def _strip_ticks(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`"):
        return value[1:-1]
    return value


def _maybe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _pos(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _nonneg(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= 0 else default


def _ratio(value: Any, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if 0 < parsed < 1 else default
