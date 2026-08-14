from __future__ import annotations

from pathlib import Path

from repo_state_agent.runtime.model import AdapterDoctorResult, AgentTurnResult
from repo_state_agent.runtime.supervisor import SupervisorOptions, supervise


def _repo(root: Path) -> None:
    (root / "docs/tasks").mkdir(parents=True)
    (root / "docs/workstreams").mkdir(parents=True)
    (root / "AGENTS.md").write_text("# Policy\n", encoding="utf-8")
    (root / "docs/tasks/T-1.md").write_text("# Task\n", encoding="utf-8")
    (root / "docs/tasks/T-2.md").write_text("# Next\n", encoding="utf-8")
    (root / "docs/workstreams/W-1.md").write_text("# Workstream\n", encoding="utf-8")
    (root / "ACTIVE.md").write_text(
        """# Active
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
Act.
## Stop Condition
Checkpoint.
## Continuation Gate
Decision: ROTATE_REQUIRED
Reason: start
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


class NoAdvanceAdapter:
    name = "fake"
    calls = 0

    def doctor(self) -> AdapterDoctorResult:
        return AdapterDoctorResult(True, "fake", "fake", "1")

    def run_turn(self, **_: object) -> AgentTurnResult:
        self.calls += 1
        return AgentTurnResult(exit_code=0, thread_id="thread")


def test_success_without_repository_checkpoint_fails_closed(tmp_path: Path) -> None:
    _repo(tmp_path)
    adapter = NoAdvanceAdapter()
    result = supervise(
        tmp_path,
        adapter,
        SupervisorOptions(max_transitions=5, quiet=True),
    )
    assert result.status == "FAILED"
    assert result.reason == "ACTIVE_STATE_NOT_ADVANCED"
    assert adapter.calls == 1
