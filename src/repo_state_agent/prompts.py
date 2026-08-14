from __future__ import annotations

from pathlib import Path

from .continuation import decide_continuation
from .parsing import parse_active

VALID_ROLES = {"builder", "reviewer", "decision", "runner", "analyst"}
VALID_MODES = {"auto", "fresh", "continue"}

ROLE_INSTRUCTIONS = {
    "builder": """Execute the active task through its stop condition.
Use V0/V1 checks while iterating and one V2 closure check when the context epoch closes.
At every task checkpoint, persist evidence, update ACTIVE.md, and run `rsaw next .`.
Continue to the next task only when the continuation result is CONTINUE.
""",
    "reviewer": """Act as a fresh reviewer.
Read the governing spec, diff or commit, tests, and evidence.
Do not preload the builder's debugging history.
Report correctness, spec compliance, regression risk, and blocking findings.
Update ACTIVE.md and stop at the review boundary.
""",
    "decision": """Use the two-pass Medium decision workflow.
Pass A decomposes facts, inferences, options, constraints, and missing evidence.
Pass B synthesizes the decision and records assumptions.
Do not implement the decision in this context epoch.
Update ACTIVE.md and stop at the decision boundary.
""",
    "runner": """Execute only the registered or authorized run described by the active task.
Preserve raw evidence and do not redesign after observing results.
Update ACTIVE.md and stop at the execution boundary.
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


def render_prompt(root: Path, role: str | None = None, mode: str = "auto") -> str:
    root = root.resolve()
    state = parse_active(root)
    selected_role = _role_for(state.current_role, state.next_role, role)
    normalized_mode = mode.strip().lower()
    if normalized_mode not in VALID_MODES:
        raise ValueError(f"Unknown mode: {mode}")

    decision = decide_continuation(state)
    if normalized_mode == "fresh":
        opening = "Resume the active RSAW workstream from repository state."
    elif normalized_mode == "continue":
        opening = "Continue the active RSAW context epoch from repository state."
    else:
        opening = (
            "Continue the active RSAW context epoch from repository state."
            if decision.may_continue
            else "Resume the active RSAW workstream from repository state."
        )

    task = state.task_spec.relative_to(root).as_posix()
    workstream = (
        state.workstream_spec.relative_to(root).as_posix()
        if state.workstream_spec and state.workstream_spec.is_relative_to(root)
        else "not configured"
    )

    return f"""Work in this repository.

{opening}

Read only:
1. AGENTS.md
2. ACTIVE.md
3. {task}

Workstream: {state.workstream_id or 'classic'} ({workstream})
Context epoch: {state.epoch_id or 'fresh-task'}
Role: {selected_role}

Treat repository state as authoritative over conversation history.
Use progressive disclosure and read additional files only when the active task requires them.
Do not reconstruct old chat history.

{ROLE_INSTRUCTIONS[selected_role]}
When the active task reaches a checkpoint:
- persist evidence and commit or record the durable state;
- activate the next task in ACTIVE.md;
- run `rsaw verify .` and `rsaw next .`;
- CONTINUE only when the gate says CONTINUE;
- otherwise stop for a fresh context, human gate, or long-running handoff.
"""
