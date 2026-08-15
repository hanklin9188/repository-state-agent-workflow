from __future__ import annotations

import fnmatch
import hashlib
import json
import re
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from ..model import ActiveState
from ..parsing import parse_active
from ..verify import verify_repository
from .adapter import AgentAdapter
from .model import AgentTurnResult, TokenUsage
from .store import RuntimeLock, RuntimeLockError, RuntimeStore, atomic_write_json, utc_now

SCHEMA_RESULT = "rsaw.checkpoint-result.v1"
SCHEMA_CAPSULE = "rsaw.semantic-capsule.v1"
SCHEMA_ENVELOPE = "rsaw.context-envelope.v1"
SCHEMA_CHECKPOINT = "rsaw.checkpoint.v6"
SCHEMA_ACTIVE = "rsaw.active.v6"
SCHEMA_REVIEW = "rsaw.review-manifest.v1"
VALID_ACTIONS = {"CONTINUE", "COMPACT", "ROTATE", "PAUSE", "COMPLETE"}
RUNTIME_EXCLUDES = (".git/", ".rsaw/runtime/", ".rsaw/state/")


@dataclass(frozen=True)
class V6Options:
    context_window_tokens: int = 128_000
    target_envelope_tokens: int = 6_000
    hard_envelope_tokens: int = 12_000
    max_exact_evidence_tokens: int = 7_000
    max_capsule_tokens: int = 2_500
    max_validation_summary_tokens: int = 1_000
    compact_candidate_ratio: float = 0.75
    compact_required_ratio: float = 0.85
    hard_turn_ceiling: int = 8
    max_transitions: int = 100
    max_total_input_tokens: int = 5_000_000
    quiet: bool = False
    dry_run: bool = False

    @classmethod
    def from_root(cls, root: Path, *, quiet: bool = False, dry_run: bool = False) -> "V6Options":
        path = root / ".rsaw/config.json"
        raw: dict[str, Any] = {}
        if path.is_file():
            value = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                raw = value
        runtime = raw.get("runtime", {}) if isinstance(raw.get("runtime", {}), dict) else {}
        v6 = runtime.get("v6", {}) if isinstance(runtime.get("v6", {}), dict) else {}
        compiler = v6.get("contextCompiler", {}) if isinstance(v6.get("contextCompiler", {}), dict) else {}
        governor = v6.get("governor", {}) if isinstance(v6.get("governor", {}), dict) else {}
        return cls(
            context_window_tokens=_pos(v6.get("contextWindowTokens"), 128_000),
            target_envelope_tokens=_pos(compiler.get("targetEnvelopeTokens"), 6_000),
            hard_envelope_tokens=_pos(compiler.get("hardEnvelopeTokens"), 12_000),
            max_exact_evidence_tokens=_pos(compiler.get("maxExactEvidenceTokens"), 7_000),
            max_capsule_tokens=_pos(compiler.get("maxSemanticCapsuleTokens"), 2_500),
            max_validation_summary_tokens=_pos(compiler.get("maxValidationSummaryTokens"), 1_000),
            compact_candidate_ratio=_ratio(governor.get("compactCandidateRatio"), 0.75),
            compact_required_ratio=_ratio(governor.get("compactRequiredRatio"), 0.85),
            hard_turn_ceiling=_pos(governor.get("hardTurnCeiling"), 8),
            max_transitions=_pos(runtime.get("max_transitions"), 100),
            max_total_input_tokens=_nonneg(runtime.get("max_total_input_tokens"), 5_000_000),
            quiet=quiet,
            dry_run=dry_run,
        )


@dataclass(frozen=True)
class TaskRef:
    task_id: str
    spec: str
    role: str

    @classmethod
    def from_value(cls, value: Any, *, default_role: str = "Builder") -> "TaskRef | None":
        if not isinstance(value, dict):
            return None
        task_id = _s(value.get("id") or value.get("taskId"))
        spec = _s(value.get("spec") or value.get("taskSpec"))
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
    def parse(cls, text: str) -> "CheckpointResult":
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
    def load(cls, root: Path, workstream_id: str) -> "SemanticCapsule":
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

    def merge(self, delta: dict[str, Any], *, checkpoint_id: str, revision: str, role: str, objective: str, evidence_refs: list[str], max_tokens: int) -> None:
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
        incoming_refs = _str_list(delta.get("evidenceRefs")) + evidence_refs
        self.evidence_refs = list(dict.fromkeys([*self.evidence_refs, *incoming_refs]))[-64:]
        self.checkpoint_id = checkpoint_id
        self.source_revision = revision
        self.role = role
        self.objective = objective
        self.next_action = _s(delta.get("nextAction")) or self.next_action
        self._prune(max_tokens)

    def _prune(self, max_tokens: int) -> None:
        self.unresolved_risks = [x for x in self.unresolved_risks if not bool(x.get("resolved"))][-24:]
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
                parts.append(f"### {component.get('name')}\nReference: {component.get('reference')}")
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
            "fresh_input_tokens": max(0, self.total_usage.input_tokens - self.total_usage.cached_input_tokens),
        }


@dataclass(frozen=True)
class V6SupervisorResult:
    status: str
    reason: str
    run_id: str
    summary_path: Path | None
    exit_code: int


EventSink = Callable[[dict[str, Any]], None]


def v6_enabled(root: Path) -> bool:
    path = root / ".rsaw/config.json"
    if not path.is_file():
        return False
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    runtime = raw.get("runtime", {}) if isinstance(raw, dict) else {}
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


def compile_context(root: Path, *, mode: str = "FRESH", options: V6Options | None = None, previous_envelope: dict[str, Any] | None = None) -> ContextEnvelope:
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
        components.append({"name": "Stable governance", "category": "stable-ref", "reference": f"sha256:{_sha_text(stable_text)}", "tokens": 0, "sha256": _sha_text(stable_text)})
    components.append(_component("Task contract", task_text, "exact"))
    if capsule.observed_facts or capsule.decisions or capsule.excluded_hypotheses or capsule.unresolved_risks:
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
    previous_digests = {c.get("sha256") for c in previous.get("components", []) if isinstance(c, dict)} if isinstance(previous, dict) else set()
    repeated = sum(int(c.get("tokens", 0)) for c in components if c.get("sha256") in previous_digests and c.get("content"))
    resend = sum(int(c.get("tokens", 0)) for c in components if c.get("category") == "exact-evidence" and c.get("sha256") in previous_digests)
    total = sum(int(c.get("tokens", 0)) for c in components)
    capsule_tokens = sum(int(c.get("tokens", 0)) for c in components if c.get("category") == "semantic")
    warnings: list[str] = []
    if total > options.target_envelope_tokens:
        warnings.append(f"envelope exceeds target: {total}>{options.target_envelope_tokens}")
    if total > options.hard_envelope_tokens:
        raise ValueError(f"context envelope exceeds hard budget: {total}>{options.hard_envelope_tokens}")
    payload = json.dumps(components, sort_keys=True, separators=(",", ":"))
    return ContextEnvelope(normalized_mode, role, state.task_id, tuple(components), total, evidence_tokens, capsule_tokens, 0, repeated, resend, _sha_text(payload), tuple(warnings))


def store_evidence(root: Path, *, kind: str, source: str, content: str) -> EvidenceHandle:
    digest = _sha_text(content)
    evidence_id = f"EV-{kind.upper()}-{digest[:16]}"
    path = root / ".rsaw/state/evidence" / f"{evidence_id}.json"
    if not path.exists():
        atomic_write_json(path, {"schemaVersion": "rsaw.evidence.v1", "evidenceId": evidence_id, "kind": kind, "source": source, "sha256": digest, "bytes": len(content.encode('utf-8')), "approxTokens": _tokens(content), "content": content})
    return EvidenceHandle(evidence_id, kind, digest, source, len(content.encode("utf-8")), _tokens(content), path.relative_to(root).as_posix())


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
        return {"changed": False, "exists": True, "path": relative, "sha256": digest}
    text = path.read_text(encoding="utf-8")
    return {"changed": True, "exists": True, "path": relative, "sha256": digest, "content": text, "approxTokens": _tokens(text)}


def governor_decision(*, current_role: str, next_role: str, requested_action: str, human_gate: str, complete: bool, estimated_occupancy_tokens: int, context_window_tokens: int, compact_candidate_ratio: float, compact_required_ratio: float, thread_turns: int, hard_turn_ceiling: int, runtime_corrupt: bool = False) -> GovernorDecision:
    occupancy = min(1.0, max(0.0, estimated_occupancy_tokens / max(1, context_window_tokens)))
    if complete or requested_action == "COMPLETE":
        return GovernorDecision("COMPLETE", "WORKSTREAM_COMPLETE", occupancy, estimated_occupancy_tokens)
    if human_gate or requested_action == "PAUSE":
        return GovernorDecision("PAUSE", "HUMAN_GATE" if human_gate else "EXPLICIT_PAUSE", occupancy, estimated_occupancy_tokens)
    if runtime_corrupt:
        return GovernorDecision("ROTATE", "RUNTIME_CORRUPTION", occupancy, estimated_occupancy_tokens)
    if _role(current_role) != _role(next_role):
        return GovernorDecision("ROTATE", "ROLE_BOUNDARY", occupancy, estimated_occupancy_tokens)
    if requested_action == "ROTATE":
        return GovernorDecision("ROTATE", "EXPLICIT_COGNITIVE_BOUNDARY", occupancy, estimated_occupancy_tokens)
    if occupancy >= compact_required_ratio:
        return GovernorDecision("COMPACT", "CONTEXT_OCCUPANCY_HARD", occupancy, estimated_occupancy_tokens)
    if requested_action == "COMPACT" or occupancy >= compact_candidate_ratio:
        return GovernorDecision("COMPACT", "CONTEXT_OCCUPANCY_PRESSURE", occupancy, estimated_occupancy_tokens)
    if hard_turn_ceiling and thread_turns >= hard_turn_ceiling:
        return GovernorDecision("COMPACT", "HARD_TURN_CEILING", occupancy, estimated_occupancy_tokens)
    return GovernorDecision("CONTINUE", "COHERENT_WORKING_CONTEXT", occupancy, estimated_occupancy_tokens)


def inspect_turn_events(result: AgentTurnResult, root: Path) -> dict[str, Any]:
    tool_calls = 0
    commands: list[dict[str, Any]] = []
    retained_output_tokens = 0
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
            if item_type in {"command_execution", "command", "shell", "shell_command", "tool_call", "mcp_tool_call", "function_call"} and event_type.endswith(".started"):
                tool_calls += 1
            if item_type in {"command_execution", "command", "shell", "shell_command"}:
                cmd = payload.get("command") or payload.get("cmd")
                if isinstance(cmd, list):
                    cmd = " ".join(str(x) for x in cmd)
                if isinstance(cmd, str) and cmd:
                    record = {"command": _one_line(cmd), "exitCode": _maybe_int(payload.get("exit_code") or payload.get("exitCode")), "eventType": event_type}
                    if not commands or commands[-1]["command"] != record["command"] or event_type.endswith(".completed"):
                        commands.append(record)
            output = payload.get("aggregated_output") or payload.get("output") or payload.get("stdout")
            if isinstance(output, str):
                retained_output_tokens += min(_tokens(output), 1000)
    return {"tool_calls": tool_calls, "commands": commands, "retained_tool_output_tokens": retained_output_tokens}


def deterministic_gate(root: Path, *, state: ActiveState, result: CheckpointResult, active_sha_before: str, changed_files: tuple[str, ...], event_info: dict[str, Any], evidence_ids: set[str]) -> GateDecision:
    errors: list[str] = []
    warnings: list[str] = []
    if _sha_file(root / "ACTIVE.md") != active_sha_before:
        errors.append("MODEL_MUTATED_ACTIVE")
    if result.outcome not in {"PASS", "COMPLETE", "BLOCKED"}:
        errors.append(f"INVALID_OUTCOME:{result.outcome}")
    reported = set(result.changed_files)
    actual = {p for p in changed_files if not p.startswith(".rsaw/")}
    if actual - reported:
        errors.append("UNREPORTED_CHANGED_FILES:" + ",".join(sorted(actual - reported)))
    contract = parse_task_contract(state.task_spec)
    allowed = contract.get("allowed_writes", [])
    if allowed:
        for path in sorted(actual):
            if not any(fnmatch.fnmatch(path, pattern) for pattern in allowed):
                errors.append(f"WRITE_OUTSIDE_SCOPE:{path}")
    command_records = [x for x in event_info.get("commands", []) if isinstance(x, dict)]
    executed = [_s(x.get("command")) for x in command_records]
    for required in contract.get("validations", []):
        matched = [
            record
            for record in command_records
            if _command_matches(required, _s(record.get("command")))
        ]
        if not matched:
            errors.append(f"VALIDATION_NOT_EXECUTED:{required}")
            continue
        completed = [
            record
            for record in matched
            if _s(record.get("eventType")).endswith(".completed")
        ]
        if any(record.get("exitCode") not in {None, 0} for record in completed):
            errors.append(f"VALIDATION_FAILED:{required}")
        elif not completed:
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
    unknown = refs - evidence_ids
    if unknown:
        errors.append("UNKNOWN_EVIDENCE_REFS:" + ",".join(sorted(unknown)))
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
    return GateDecision(not errors, tuple(errors), tuple(warnings), tuple(sorted(actual)), tuple(executed))


def parse_task_contract(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"allowed_writes": [], "validations": []}
    text = path.read_text(encoding="utf-8")
    return {
        "allowed_writes": _section_bullets(text, "Allowed Writes"),
        "validations": [_strip_ticks(x) for x in _section_bullets(text, "Validation")],
    }


def supervise_v6(root: Path, adapter: AgentAdapter, options: V6Options, *, event_sink: EventSink | None = None) -> V6SupervisorResult:
    root = root.resolve()
    verification = verify_repository(root)
    if not verification.ok:
        return V6SupervisorResult("FAILED", "REPOSITORY_VERIFICATION_FAILED", "", None, 23)
    state = parse_active(root)
    run_id = f"rsaw-v6-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    store = RuntimeStore(root, run_id)
    summary = V6Summary(run_id=run_id, repository=str(root), started_at=utc_now(), workstream=state.workstream_id)
    _save_v6_summary(store, summary)
    _emit(store, event_sink, {"type": "v6.supervisor.started", "run_id": run_id, "workstream": state.workstream_id, "task": state.task_id})

    def finish(status: str, reason: str, code: int) -> V6SupervisorResult:
        current = _safe_state(root, state)
        summary.status = status
        summary.reason = reason
        summary.final_task = current.task_id
        summary.human_gate = current.human_gate
        summary.ended_at = utc_now()
        _save_v6_summary(store, summary)
        _emit(store, event_sink, {"type": "v6.supervisor.terminal", "status": status, "reason": reason})
        return V6SupervisorResult(status, reason, run_id, store.summary_path, code)

    if state.human_gate:
        return finish("PAUSED", "HUMAN_GATE", 20)
    if options.dry_run:
        try:
            envelope = compile_context(root, mode="FRESH", options=options)
        except ValueError as exc:
            return finish("FAILED", f"CONTEXT_COMPILATION_FAILED:{exc}", 27)
        _emit(store, event_sink, {"type": "v6.context.compiled", **envelope.to_dict()})
        return finish("DRY_RUN", "V6_READY", 0)

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
                    envelope = compile_context(root, mode=next_mode, options=options, previous_envelope=previous_envelope)
                except ValueError as exc:
                    return finish("FAILED", f"CONTEXT_COMPILATION_FAILED:{exc}", 27)
                envelope_path = root / ".rsaw/state/envelopes" / run_id / f"turn-{summary.agent_turns + 1:04d}.json"
                atomic_write_json(envelope_path, envelope.to_dict())
                _emit(store, event_sink, {"type": "v6.context.compiled", **envelope.to_dict()})
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
                _emit(store, event_sink, {"type": "v6.agent.turn.started", "turn": summary.agent_turns, "mode": next_mode, "task": state.task_id, "role": state.current_role})
                turn = adapter.run_turn(prompt=prompt, root=root, run_dir=store.run_dir, turn_index=summary.agent_turns, thread_id=thread_id, environment={"RSAW_SUPERVISED": "1", "RSAW_V6": "1", "RSAW_RUN_ID": run_id, "RSAW_TASK_ID": state.task_id, "RSAW_ROLE": state.current_role or state.next_role})
                summary.total_usage = summary.total_usage + turn.usage
                if not turn.ok:
                    return finish("FAILED", f"AGENT_TURN_FAILED:{turn.error or turn.exit_code}", 22)
                event_info = inspect_turn_events(turn, root)
                summary.tool_calls += int(event_info["tool_calls"])
                epoch_tokens_estimate += turn.latest_turn_usage.output_tokens + int(event_info["retained_tool_output_tokens"])
                try:
                    result = CheckpointResult.parse(turn.last_message)
                except ValueError as exc:
                    return finish("FAILED", f"CHECKPOINT_RESULT_INVALID:{exc}", 28)
                dirty_after = _dirty_hashes(root)
                changed = tuple(sorted(path for path in set(dirty_before) | set(dirty_after) if dirty_before.get(path) != dirty_after.get(path) and not _excluded(path)))

                evidence_handles: list[EvidenceHandle] = []
                for path in changed:
                    file_path = root / path
                    if file_path.is_file() and file_path.stat().st_size <= 128_000:
                        content = file_path.read_text(encoding="utf-8", errors="replace")
                        evidence_handles.append(store_evidence(root, kind="file", source=path, content=content))
                command_summary = json.dumps(event_info.get("commands", []), indent=2)
                if command_summary != "[]":
                    evidence_handles.append(store_evidence(root, kind="validation", source=f"turn-{summary.agent_turns}", content=command_summary))
                evidence_ids = {handle.evidence_id for handle in evidence_handles}
                gate = deterministic_gate(root, state=state, result=result, active_sha_before=active_sha_before, changed_files=changed, event_info=event_info, evidence_ids=evidence_ids)
                _emit(store, event_sink, {"type": "v6.gate", **gate.to_dict()})
                if not gate.accepted:
                    return finish("FAILED", "DETERMINISTIC_GATE_REJECTED:" + ";".join(gate.errors), 29)

                checkpoint_index += 1
                checkpoint_id = f"CP-{checkpoint_index:04d}"
                revision = _git_revision(root)
                capsule = SemanticCapsule.load(root, state.workstream_id)
                capsule.merge(result.capsule_delta, checkpoint_id=checkpoint_id, revision=revision, role=state.current_role or state.next_role, objective=result.summary or state.next_action, evidence_refs=[h.evidence_id for h in evidence_handles], max_tokens=options.max_capsule_tokens)
                capsule_path = capsule.save(root)
                summary.semantic_capsule_tokens += _tokens(json.dumps(capsule.to_dict(), sort_keys=True))
                complete = result.requested_action == "COMPLETE"
                next_role = result.next_task.role if result.next_task else (state.next_role or state.current_role)
                decision = governor_decision(current_role=state.current_role or state.next_role, next_role=next_role, requested_action=result.requested_action, human_gate=result.human_gate, complete=complete, estimated_occupancy_tokens=epoch_tokens_estimate, context_window_tokens=options.context_window_tokens, compact_candidate_ratio=options.compact_candidate_ratio, compact_required_ratio=options.compact_required_ratio, thread_turns=thread_turns, hard_turn_ceiling=options.hard_turn_ceiling)
                summary.occupancy_samples.append(decision.occupancy_ratio)
                if decision.action == "COMPACT":
                    summary.context_compactions += 1
                elif decision.action == "ROTATE":
                    summary.role_rotations += 1
                _emit(store, event_sink, {"type": "v6.governor", **decision.to_dict()})

                review_manifest_path = None
                if decision.action == "ROTATE" and _role(next_role) == "reviewer":
                    review_manifest_path = _write_review_manifest(root, checkpoint_id, state, result, evidence_handles, revision)
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
                    "reviewManifestRef": review_manifest_path.relative_to(root).as_posix() if review_manifest_path else None,
                }
                checkpoint_path = root / ".rsaw/state/checkpoints" / f"{checkpoint_id}.json"
                if checkpoint_path.exists():
                    return finish("FAILED", f"CHECKPOINT_ALREADY_EXISTS:{checkpoint_id}", 29)
                atomic_write_json(checkpoint_path, checkpoint)
                _write_sha_sidecar(checkpoint_path)
                summary.deterministic_operations += 5
                _write_active_pointer(root, state, result, decision, checkpoint_id, capsule_path, revision)
                _update_active_markdown(root, state, result, decision, checkpoint_id)
                post = verify_repository(root)
                if not post.ok:
                    return finish("FAILED", "POST_ADVANCE_REPOSITORY_INVALID:" + ";".join(post.errors), 23)
                summary.checkpoints_observed += 1
                _emit(store, event_sink, {"type": "v6.checkpoint.sealed", "checkpoint": checkpoint_id, "task": state.task_id, "nextAction": decision.action})
                _save_v6_summary(store, summary)

                if options.max_total_input_tokens and summary.total_usage.input_tokens >= options.max_total_input_tokens:
                    return finish("LIMIT_REACHED", "MAX_TOTAL_INPUT_TOKENS", 24)
                if decision.action == "COMPLETE":
                    return finish("COMPLETE", decision.reason, 0)
                if decision.action == "PAUSE":
                    return finish("PAUSED", decision.reason, 20)
                if decision.action in {"COMPACT", "ROTATE"}:
                    thread_id = None
                    next_mode = "COMPACT" if decision.action == "COMPACT" else ("REVIEW" if _role(next_role) == "reviewer" else "FRESH")
                    previous_envelope = envelope.to_dict()
                else:
                    thread_id = turn.thread_id
                    summary.resumed_turns += 1
                    next_mode = "CONTINUE"
                    previous_envelope = envelope.to_dict()
            return finish("LIMIT_REACHED", "MAX_TRANSITIONS", 24)
    except RuntimeLockError as exc:
        return finish("FAILED", f"SUPERVISOR_LOCKED:{exc}", 25)
    except KeyboardInterrupt:
        return finish("PAUSED", "SUPERVISOR_INTERRUPTED", 20)


def v6_efficiency_view(summary: dict[str, Any]) -> dict[str, Any]:
    usage = summary.get("total_usage", {}) if isinstance(summary.get("total_usage"), dict) else {}
    input_tokens = _maybe_int(usage.get("input_tokens")) or 0
    cached = min(input_tokens, _maybe_int(usage.get("cached_input_tokens")) or 0)
    successful = _maybe_int(summary.get("checkpoints_observed")) or 0
    return {
        **summary,
        "fresh_input_tokens": max(0, input_tokens - cached),
        "input_tokens_per_successful_checkpoint": round(input_tokens / successful, 2) if successful else None,
        "cached_input_tokens_per_successful_checkpoint": round(cached / successful, 2) if successful else None,
        "fresh_input_tokens_per_successful_checkpoint": round((input_tokens - cached) / successful, 2) if successful else None,
        "model_calls_per_successful_checkpoint": round((_maybe_int(summary.get("model_calls")) or 0) / successful, 3) if successful else None,
        "tool_calls_per_successful_checkpoint": round((_maybe_int(summary.get("tool_calls")) or 0) / successful, 3) if successful else None,
    }


def synthetic_acceptance(root: Path, checkpoints: int) -> dict[str, Any]:
    if checkpoints not in {4, 16, 64}:
        raise ValueError("synthetic acceptance supports 4, 16, or 64 checkpoints")
    context_window = 128_000
    occupancy = 4_000
    compactions = 0
    rotations = 0
    continues = 0
    complete_count = 0
    action_trace: list[str] = []
    for index in range(1, checkpoints + 1):
        if checkpoints == 4:
            if index <= 2:
                current_role = next_role = "Builder"
            elif index == 3:
                current_role, next_role = "Builder", "Reviewer"
            else:
                current_role = next_role = "Reviewer"
        else:
            position = (index - 1) % 8
            current_role = "Reviewer" if position == 7 else "Builder"
            next_role = "Reviewer" if position == 6 else "Builder"
        decision = governor_decision(
            current_role=current_role,
            next_role=next_role,
            requested_action="CONTINUE",
            human_gate="",
            complete=index == checkpoints,
            estimated_occupancy_tokens=occupancy,
            context_window_tokens=context_window,
            compact_candidate_ratio=0.75,
            compact_required_ratio=0.85,
            thread_turns=((index - 1) % 8) + 1,
            hard_turn_ceiling=8,
        )
        action_trace.append(decision.action)
        if decision.action == "COMPACT":
            compactions += 1
            occupancy = 5_000
        elif decision.action == "ROTATE":
            rotations += 1
            occupancy = 5_000
        elif decision.action == "CONTINUE":
            continues += 1
            occupancy += 20_000
        elif decision.action == "COMPLETE":
            complete_count += 1
    expected = (
        rotations >= 1 and compactions == 0
        if checkpoints == 4
        else rotations >= 1 and compactions >= 1
    )
    return {
        "checkpoints": checkpoints,
        "continues": continues,
        "compactions": compactions,
        "rotations": rotations,
        "completes": complete_count,
        "manualRelay": 0,
        "aggregateInputUsedAsOccupancy": False,
        "actionTrace": action_trace,
        "pass": expected and complete_count == 1,
    }


def _v6_prompt(state: ActiveState, envelope: ContextEnvelope) -> str:
    return f"""RSAW v0.6 SUPERVISED CHECKPOINT\n\nRepository state is authoritative. The supervisor owns ACTIVE.md, checkpoint numbering, state advancement, checksums, and lifecycle decisions.\n\nHARD RULES\n- Do NOT edit ACTIVE.md.\n- Do NOT run advance.py or any RSAW state-advancement command.\n- Do semantic engineering work for exactly the active task.\n- Use the compiled context below before doing repository rediscovery.\n- Run task-relevant validation.\n- Do not expose hidden chain-of-thought.\n- Your FINAL MESSAGE must be exactly one JSON object matching rsaw.checkpoint-result.v1.\n\nACTIVE TASK: {state.task_id}\nROLE: {state.current_role or state.next_role}\nCONTEXT MODE: {envelope.mode}\nENVELOPE SHA256: {envelope.sha256}\n\n{envelope.prompt_text()}\n\nFINAL JSON CONTRACT\n{{\n  \"schemaVersion\": \"rsaw.checkpoint-result.v1\",\n  \"outcome\": \"PASS|BLOCKED|COMPLETE\",\n  \"summary\": \"concise factual checkpoint result\",\n  \"changedFiles\": [\"path\"],\n  \"validations\": [{{\"command\": \"...\", \"status\": \"PASS|FAIL\"}}],\n  \"artifacts\": [{{\"path\": \"...\", \"sha256\": \"optional\"}}],\n  \"semanticCapsuleDelta\": {{\"observedFacts\": [], \"decisions\": [], \"excludedHypotheses\": [], \"evidenceRefs\": [], \"unresolvedRisks\": [], \"codeRelations\": [], \"validationStatus\": [], \"nextAction\": \"...\"}},\n  \"nextTask\": {{\"id\": \"T-next\", \"spec\": \"docs/tasks/T-next.md\", \"role\": \"Builder\"}},\n  \"followingTask\": null,\n  \"nextAction\": \"...\",\n  \"stopCondition\": \"...\",\n  \"requestedAction\": \"CONTINUE|COMPACT|ROTATE|PAUSE|COMPLETE\",\n  \"transitionReason\": \"...\",\n  \"humanGate\": \"\"\n}}\n"""


def _write_review_manifest(root: Path, checkpoint_id: str, state: ActiveState, result: CheckpointResult, handles: list[EvidenceHandle], revision: str) -> Path:
    path = root / ".rsaw/state/reviews" / f"{checkpoint_id}.json"
    atomic_write_json(path, {"schemaVersion": SCHEMA_REVIEW, "checkpointId": checkpoint_id, "sourceRevision": revision, "claim": result.summary, "task": state.task_id, "changedFiles": list(result.changed_files), "acceptance": state.stop_condition, "evidence": [h.to_dict() for h in handles], "knownRisks": _obj_list(result.capsule_delta.get("unresolvedRisks")), "scope": "changed-files-and-bound-evidence", "escalationRequiredForFullRepositoryDiscovery": True})
    return path


def _write_active_pointer(root: Path, state: ActiveState, result: CheckpointResult, decision: GovernorDecision, checkpoint_id: str, capsule_path: Path, revision: str) -> None:
    next_task = result.next_task
    atomic_write_json(root / ".rsaw/state/active.json", {"schemaVersion": SCHEMA_ACTIVE, "workstreamId": state.workstream_id, "taskId": next_task.task_id if next_task else state.task_id, "taskSpec": next_task.spec if next_task else state.task_spec.relative_to(root).as_posix(), "role": next_task.role if next_task else state.current_role, "sourceRevision": revision, "checkpointRef": f".rsaw/state/checkpoints/{checkpoint_id}.json", "semanticCapsuleRef": capsule_path.relative_to(root).as_posix(), "nextAction": result.next_action, "transition": decision.action, "transitionReason": decision.reason})


def _update_active_markdown(root: Path, state: ActiveState, result: CheckpointResult, decision: GovernorDecision, checkpoint_id: str) -> None:
    path = root / "ACTIVE.md"
    text = path.read_text(encoding="utf-8")
    next_task = result.next_task
    if decision.action == "COMPLETE":
        continuation = "COMPLETE"
        active_id = state.task_id
        active_spec = state.task_spec.relative_to(root).as_posix()
        role = state.current_role or state.next_role
    else:
        assert next_task is not None
        active_id, active_spec, role = next_task.task_id, next_task.spec, next_task.role
        continuation = "ROTATE_REQUIRED" if decision.action == "ROTATE" else ("STOP_REQUIRED" if decision.action == "PAUSE" else "CONTINUE_ALLOWED")
    following = result.following_task
    text = _replace_section(text, "Context Epoch", f"ID: {state.epoch_id or 'E-v6'}\nRole: {role}")
    text = _replace_section(text, "Active Task", f"ID: {active_id}\nSpec: {active_spec}")
    text = _replace_section(text, "Required Reads", f"- AGENTS.md\n- ACTIVE.md\n- {active_spec}")
    text = _replace_section(text, "Human Gate", result.human_gate or "None.")
    text = _replace_section(text, "Next Exact Action", result.next_action or "Continue from the sealed checkpoint.")
    text = _replace_section(text, "Stop Condition", result.stop_condition or "Task acceptance criteria are satisfied.")
    text = _replace_section(text, "Continuation Gate", f"Decision: {continuation}\nReason: {decision.action}:{decision.reason}; checkpoint={checkpoint_id}")
    if following:
        text = _replace_section(text, "Next Task", f"ID: {following.task_id}\nSpec: {following.spec}")
        text = _replace_section(text, "Next Session Role", following.role)
    elif next_task and decision.action != "COMPLETE":
        text = _replace_section(text, "Next Task", f"ID: {next_task.task_id}\nSpec: {next_task.spec}")
        text = _replace_section(text, "Next Session Role", next_task.role)
    path.write_text(text, encoding="utf-8")


def _checkpoint_result_dict(result: CheckpointResult) -> dict[str, Any]:
    return {"schemaVersion": result.schema_version, "outcome": result.outcome, "summary": result.summary, "changedFiles": list(result.changed_files), "validations": list(result.validations), "artifacts": list(result.artifacts), "semanticCapsuleDelta": result.capsule_delta, "nextTask": asdict(result.next_task) if result.next_task else None, "followingTask": asdict(result.following_task) if result.following_task else None, "nextAction": result.next_action, "stopCondition": result.stop_condition, "requestedAction": result.requested_action, "transitionReason": result.transition_reason, "humanGate": result.human_gate}


def _save_v6_summary(store: RuntimeStore, summary: V6Summary) -> None:
    atomic_write_json(store.summary_path, summary.to_dict())
    atomic_write_json(store.latest_path, {"run_id": summary.run_id, "summary": str(store.summary_path.relative_to(store.root)), "runtimeSchema": "rsaw.runtime-summary.v6"})


def _emit(store: RuntimeStore, sink: EventSink | None, event: dict[str, Any]) -> None:
    store.append_event(event)
    if sink:
        try:
            sink(event)
        except Exception:
            pass


def _dirty_hashes(root: Path) -> dict[str, str]:
    result = subprocess.run(["git", "status", "--porcelain=v1", "-z"], cwd=root, check=False, capture_output=True)
    paths: set[str] = set()
    for entry in result.stdout.decode("utf-8", errors="replace").split("\0"):
        if not entry:
            continue
        path = entry[3:] if len(entry) >= 4 else ""
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path and not _excluded(path):
            paths.add(path)
    hashes: dict[str, str] = {}
    for rel in paths:
        path = root / rel
        hashes[rel] = _sha_file(path) if path.is_file() else "<missing>"
    return hashes


def _excluded(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return any(normalized.startswith(prefix) for prefix in RUNTIME_EXCLUDES)


def _git_revision(root: Path) -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=False, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def _next_checkpoint_index(root: Path) -> int:
    directory = root / ".rsaw/state/checkpoints"
    maximum = 0
    if directory.is_dir():
        for path in directory.glob("CP-*.json"):
            match = re.fullmatch(r"CP-(\d+)\.json", path.name)
            if match:
                maximum = max(maximum, int(match.group(1)))
    return maximum


def _write_sha_sidecar(path: Path) -> None:
    path.with_suffix(path.suffix + ".sha256").write_text(_sha_file(path) + "\n", encoding="utf-8")


def _replace_section(text: str, heading: str, body: str) -> str:
    pattern = re.compile(rf"(^##\s+{re.escape(heading)}\s*$\n)(.*?)(?=^##\s+|\Z)", re.MULTILINE | re.DOTALL | re.IGNORECASE)
    replacement = rf"\1\n{body.strip()}\n\n"
    if pattern.search(text):
        return pattern.sub(replacement, text, count=1)
    return text.rstrip() + f"\n\n## {heading}\n\n{body.strip()}\n"


def _extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        start, end = stripped.find("{"), stripped.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("final message does not contain a JSON object") from None
        try:
            value = json.loads(stripped[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid checkpoint JSON: {exc}") from None
    if not isinstance(value, dict):
        raise ValueError("checkpoint JSON must be an object")
    return value


def _component(name: str, content: str, category: str) -> dict[str, Any]:
    return {"name": name, "category": category, "content": content, "tokens": _tokens(content), "sha256": _sha_text(content)}


def _merge_semantic(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for item in [*existing, *incoming]:
        key = _s(item.get("id")) or _sha_text(json.dumps(item, sort_keys=True))[:16]
        if key not in by_id:
            order.append(key)
        by_id[key] = item
    return [by_id[key] for key in order]


def _section_bullets(text: str, heading: str) -> list[str]:
    match = re.search(rf"^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)", text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    if not match:
        return []
    return [line.strip()[2:].strip() for line in match.group(1).splitlines() if line.strip().startswith("- ")]


def _command_matches(required: str, actual: str) -> bool:
    r = " ".join(_strip_ticks(required).split())
    a = " ".join(actual.split())
    return bool(r) and (r == a or r in a)


def _strip_ticks(value: str) -> str:
    return value.strip().strip("`")


def _bounded_file(path: Path, max_bytes: int) -> str:
    if not path.is_file():
        return ""
    raw = path.read_bytes()
    return raw[:max_bytes].decode("utf-8", errors="replace")


def _sha_file(path: Path) -> str:
    if not path.is_file():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _tokens(text: str) -> int:
    return (len(text) + 3) // 4


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value or "classic").strip("-") or "classic"


def _role(value: str) -> str:
    return value.strip().lower().replace("_", "-")


def _s(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _one_line(value: str) -> str:
    return " ".join(value.split())


def _obj_list(value: Any) -> list[dict[str, Any]]:
    return [dict(x) for x in value if isinstance(x, dict)] if isinstance(value, list) else []


def _str_list(value: Any) -> list[str]:
    return [x for x in value if isinstance(x, str) and x] if isinstance(value, list) else []


def _maybe_int(value: Any) -> int | None:
    return int(value) if isinstance(value, int | float) and not isinstance(value, bool) else None


def _pos(value: Any, default: int) -> int:
    parsed = _maybe_int(value)
    return parsed if parsed is not None and parsed > 0 else default


def _nonneg(value: Any, default: int) -> int:
    parsed = _maybe_int(value)
    return parsed if parsed is not None and parsed >= 0 else default


def _ratio(value: Any, default: float) -> float:
    if isinstance(value, int | float) and not isinstance(value, bool) and 0 <= float(value) <= 1:
        return float(value)
    return default


def _safe_state(root: Path, fallback: ActiveState) -> ActiveState:
    try:
        return parse_active(root)
    except Exception:
        return fallback
