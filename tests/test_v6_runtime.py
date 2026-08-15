from __future__ import annotations

import hashlib
import json
from pathlib import Path

from repo_state_agent.model import ActiveState
from repo_state_agent.runtime.v6 import (
    SCHEMA_RESULT,
    CheckpointResult,
    SemanticCapsule,
    V6Options,
    compile_context,
    deterministic_gate,
    governor_decision,
    migrate_v6,
    read_if_changed,
    store_evidence,
    synthetic_acceptance,
)


def _repo(root: Path) -> None:
    (root / ".rsaw").mkdir(parents=True, exist_ok=True)
    (root / "docs/tasks").mkdir(parents=True, exist_ok=True)
    (root / "docs/workstreams").mkdir(parents=True, exist_ok=True)
    (root / "AGENTS.md").write_text("# Policy\nDo not mutate ACTIVE from the model.\n", encoding="utf-8")
    (root / "docs/workstreams/W.md").write_text("# W — Workstream\n", encoding="utf-8")
    (root / "docs/tasks/T1.md").write_text(
        """# T1 — Implement

## Allowed Writes
- src/**
- tests/**

## Validation
- `python -m pytest -q`
""",
        encoding="utf-8",
    )
    (root / "docs/tasks/T2.md").write_text("# T2 — Review\n", encoding="utf-8")
    (root / "docs/tasks/T3.md").write_text("# T3 — Close\n", encoding="utf-8")
    (root / "ACTIVE.md").write_text(
        """# Active Handoff

## Workstream
ID: W
Spec: docs/workstreams/W.md

## Context Epoch
ID: E-1
Role: Builder

## Active Task
ID: T1
Spec: docs/tasks/T1.md

## Required Reads
- AGENTS.md
- ACTIVE.md
- docs/tasks/T1.md

## Human Gate
None.

## Next Exact Action
Implement the scoped change.

## Stop Condition
Focused validation passes.

## Continuation Gate
Decision: CONTINUE_ALLOWED
Reason: same builder epoch

## Next Task
ID: T2
Spec: docs/tasks/T2.md

## Next Session Role
Reviewer

## Recommended Reasoning
Medium
""",
        encoding="utf-8",
    )
    (root / ".rsaw/config.json").write_text(
        json.dumps({"schema_version": 2, "runtime": {"max_transitions": 100}}),
        encoding="utf-8",
    )


def _result(**overrides: object) -> CheckpointResult:
    payload: dict[str, object] = {
        "schemaVersion": SCHEMA_RESULT,
        "outcome": "PASS",
        "summary": "implementation complete",
        "changedFiles": ["src/a.py"],
        "validations": [{"command": "python -m pytest -q", "status": "PASS"}],
        "artifacts": [],
        "semanticCapsuleDelta": {
            "observedFacts": [{"id": "F-1", "claim": "a"}],
            "decisions": [],
            "excludedHypotheses": [],
            "evidenceRefs": [],
            "unresolvedRisks": [],
            "codeRelations": [],
            "validationStatus": [],
            "nextAction": "review",
        },
        "nextTask": {"id": "T2", "spec": "docs/tasks/T2.md", "role": "Reviewer"},
        "followingTask": {"id": "T3", "spec": "docs/tasks/T3.md", "role": "Builder"},
        "nextAction": "Review the sealed change.",
        "stopCondition": "Independent review completes.",
        "requestedAction": "CONTINUE",
        "transitionReason": "builder checkpoint",
        "humanGate": "",
    }
    payload.update(overrides)
    return CheckpointResult.parse(json.dumps(payload))


def test_checkpoint_result_is_typed_and_rejects_unknown_lifecycle() -> None:
    result = _result()
    assert result.next_task is not None
    assert result.next_task.role == "Reviewer"
    bad = json.loads(json.dumps({
        "schemaVersion": SCHEMA_RESULT,
        "outcome": "PASS",
        "changedFiles": [],
        "validations": [],
        "artifacts": [],
        "semanticCapsuleDelta": {},
        "requestedAction": "RESET",
    }))
    try:
        CheckpointResult.parse(json.dumps(bad))
    except ValueError as exc:
        assert "invalid requestedAction" in str(exc)
    else:
        raise AssertionError("unknown lifecycle action was accepted")


def test_migration_preserves_active_byte_for_byte(tmp_path: Path) -> None:
    _repo(tmp_path)
    before = (tmp_path / "ACTIVE.md").read_bytes()
    plan = migrate_v6(tmp_path, apply=False)
    assert plan["preservesActive"] is True
    result = migrate_v6(tmp_path, apply=True)
    assert result["status"] == "MIGRATED"
    assert (tmp_path / "ACTIVE.md").read_bytes() == before
    raw = json.loads((tmp_path / ".rsaw/config.json").read_text())
    assert raw["schema_version"] == 3
    assert raw["runtime"]["v6"]["enabled"] is True
    assert raw["runtime"]["v6"]["governor"]["useAggregateProviderInputAsOccupancy"] is False


def test_context_compiler_uses_stable_reference_on_continue(tmp_path: Path) -> None:
    _repo(tmp_path)
    migrate_v6(tmp_path, apply=True)
    fresh = compile_context(tmp_path, mode="FRESH")
    continued = compile_context(tmp_path, mode="CONTINUE", previous_envelope=fresh.to_dict())
    stable_fresh = fresh.components[0]
    stable_continue = continued.components[0]
    assert stable_fresh["category"] == "stable"
    assert "content" in stable_fresh
    assert stable_continue["category"] == "stable-ref"
    assert "content" not in stable_continue
    assert continued.total_tokens < fresh.total_tokens


def test_read_if_changed_and_evidence_handles_are_content_addressed(tmp_path: Path) -> None:
    _repo(tmp_path)
    path = tmp_path / "src/a.py"
    path.parent.mkdir(parents=True)
    path.write_text("x = 1\n", encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert read_if_changed(tmp_path, "src/a.py", digest)["changed"] is False
    path.write_text("x = 2\n", encoding="utf-8")
    changed = read_if_changed(tmp_path, "src/a.py", digest)
    assert changed["changed"] is True
    first = store_evidence(tmp_path, kind="file", source="src/a.py", content="x = 2\n")
    second = store_evidence(tmp_path, kind="file", source="src/a.py", content="x = 2\n")
    assert first.evidence_id == second.evidence_id
    assert (tmp_path / first.store_path).is_file()


def test_semantic_capsule_deduplicates_and_prunes(tmp_path: Path) -> None:
    capsule = SemanticCapsule("W")
    capsule.merge(
        {
            "observedFacts": [
                {"id": "F-1", "claim": "old"},
                {"id": "F-1", "claim": "new"},
            ],
            "unresolvedRisks": [
                {"id": "R-1", "claim": "done", "resolved": True},
                {"id": "R-2", "claim": "open"},
            ],
        },
        checkpoint_id="CP-1",
        revision="abc",
        role="Builder",
        objective="test",
        evidence_refs=[],
        max_tokens=2500,
    )
    assert capsule.observed_facts == [{"id": "F-1", "claim": "new"}]
    assert [risk["id"] for risk in capsule.unresolved_risks] == ["R-2"]
    capsule.save(tmp_path)
    assert SemanticCapsule.load(tmp_path, "W").checkpoint_id == "CP-1"


def test_governor_separates_continue_compact_rotate_and_pause() -> None:
    common = dict(
        requested_action="CONTINUE",
        human_gate="",
        complete=False,
        context_window_tokens=100_000,
        compact_candidate_ratio=0.75,
        compact_required_ratio=0.85,
        hard_turn_ceiling=8,
    )
    assert governor_decision(current_role="Builder", next_role="Builder", estimated_occupancy_tokens=50_000, thread_turns=2, **common).action == "CONTINUE"
    assert governor_decision(current_role="Builder", next_role="Builder", estimated_occupancy_tokens=78_000, thread_turns=2, **common).action == "COMPACT"
    assert governor_decision(current_role="Builder", next_role="Reviewer", estimated_occupancy_tokens=50_000, thread_turns=2, **common).action == "ROTATE"
    paused = governor_decision(current_role="Builder", next_role="Builder", estimated_occupancy_tokens=50_000, thread_turns=2, **{**common, "human_gate": "APPROVAL"})
    assert paused.action == "PAUSE"


def test_deterministic_gate_rejects_model_owned_active_mutation(tmp_path: Path) -> None:
    _repo(tmp_path)
    state = ActiveState(
        root=tmp_path,
        active_path=tmp_path / "ACTIVE.md",
        task_id="T1",
        task_spec=tmp_path / "docs/tasks/T1.md",
        required_reads=(),
        next_action="implement",
        stop_condition="pass",
        next_role="Reviewer",
        reasoning="Medium",
        workstream_id="W",
        epoch_id="E-1",
        current_role="Builder",
    )
    before = hashlib.sha256((tmp_path / "ACTIVE.md").read_bytes()).hexdigest()
    (tmp_path / "ACTIVE.md").write_text("model changed state\n", encoding="utf-8")
    gate = deterministic_gate(
        tmp_path,
        state=state,
        result=_result(changedFiles=[]),
        active_sha_before=before,
        changed_files=(),
        event_info={"commands": [{"command": "python -m pytest -q"}]},
        evidence_ids=set(),
    )
    assert gate.accepted is False
    assert "MODEL_MUTATED_ACTIVE" in gate.errors


def test_synthetic_horizons_preserve_zero_manual_relay(tmp_path: Path) -> None:
    for horizon in (4, 16, 64):
        result = synthetic_acceptance(tmp_path, horizon)
        assert result["pass"] is True
        assert result["manualRelay"] == 0
        assert result["aggregateInputUsedAsOccupancy"] is False
