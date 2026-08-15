from __future__ import annotations

import json
from pathlib import Path

from repo_state_agent.runtime.model import AdapterDoctorResult
from repo_state_agent.runtime.v6 import V6Options, supervise_v6


class _UnusedAdapter:
    name = "unused"

    def doctor(self) -> AdapterDoctorResult:
        return AdapterDoctorResult(ok=True, adapter=self.name, binary="unused")

    def run_turn(self, **_kwargs):  # pragma: no cover - dry-run must never call this
        raise AssertionError("dry-run invoked the agent")


def _repo(root: Path) -> None:
    (root / ".rsaw").mkdir(parents=True)
    (root / "docs/tasks").mkdir(parents=True)
    (root / "docs/workstreams").mkdir(parents=True)
    (root / "AGENTS.md").write_text("# Policy\n", encoding="utf-8")
    (root / "docs/tasks/T1.md").write_text("# T1\n", encoding="utf-8")
    (root / "docs/workstreams/W.md").write_text("# W\n", encoding="utf-8")
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
Inspect the task.

## Stop Condition
Inspection completes.

## Continuation Gate
Decision: CONTINUE_ALLOWED
Reason: same role

## Next Task
ID: T1
Spec: docs/tasks/T1.md

## Next Session Role
Builder

## Recommended Reasoning
Medium
""",
        encoding="utf-8",
    )
    (root / ".rsaw/config.json").write_text(
        json.dumps(
            {
                "schema_version": 4,
                "runtime": {
                    "v6": {"enabled": True},
                    "max_transitions": 4,
                },
            }
        ),
        encoding="utf-8",
    )


def test_dry_run_uses_v07_identity(tmp_path: Path) -> None:
    _repo(tmp_path)
    result = supervise_v6(
        tmp_path,
        _UnusedAdapter(),
        V6Options(dry_run=True),
    )

    assert result.status == "DRY_RUN"
    assert result.reason == "V7_READY"
    assert result.exit_code == 0
    assert result.run_id.startswith("rsaw-v7-")
    assert result.summary_path is not None

    summary = json.loads(result.summary_path.read_text(encoding="utf-8"))
    assert summary["run_id"] == result.run_id

    events = (tmp_path / ".rsaw/runtime" / result.run_id / "supervisor-events.jsonl").read_text(
        encoding="utf-8"
    )
    assert '"runtime": "v0.7"' in events
