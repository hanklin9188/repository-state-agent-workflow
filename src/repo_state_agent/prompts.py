from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .continuation import decide_continuation
from .parsing import parse_active

if TYPE_CHECKING:
    from .runtime.config import RuntimeConfig
    from .runtime.context import ContextPlan


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
    from .runtime.config import load_runtime_config
    from .runtime.context import build_context_plan

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

Repository state is authoritative over conversation history. Do not reconstruct old
chat history. Keep the workstream durable and the model context bounded. Use
progressive disclosure: read only the ordered context plan, then expand only when
the active task requires evidence.

{opening}

{reads}

Workstream: {state.workstream_id or "classic"} ({workstream})
Context epoch: {state.epoch_id or "fresh-task"}
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
            "Read only:",
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

    lines = ["Read only:", "Use this ordered bootstrap context:", "", "Stable prefix:"]
    lines.extend(f"{index}. {path}" for index, path in enumerate(stable, 1))
    lines.append("")
    lines.append("Dynamic authority:")
    lines.extend(f"{index}. {path}" for index, path in enumerate(dynamic, 1))
    return "\n".join(lines)
