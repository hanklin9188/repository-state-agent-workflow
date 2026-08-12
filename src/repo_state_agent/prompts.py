from __future__ import annotations

from pathlib import Path

from .parsing import parse_active

BASE = """Work in this repository.

Read only:
1. AGENTS.md
2. ACTIVE.md
3. {task}

Treat repository state as authoritative over conversation history.
Use progressive disclosure and read additional files only when required.
"""


def render_prompt(root: Path, role: str) -> str:
    state = parse_active(root.resolve())
    task = state.task_spec.relative_to(root.resolve()).as_posix()
    intro = BASE.format(task=task)

    if role == "builder":
        return intro + """
Execute exactly the active task.
Use targeted validation while iterating and closure validation when stable.
Reuse verified evidence and do not repeat completed work.
When complete or blocked, update ACTIVE.md and stop.
"""
    if role == "reviewer":
        return intro + """
Act as a fresh reviewer.
Read the governing spec, diff or commit, tests, and evidence.
Do not preload the builder's debugging history.
Report correctness, spec compliance, regression risk, and blocking findings.
Update ACTIVE.md with the review result and stop.
"""
    if role == "decision":
        return intro + """
Use the two-pass Medium decision workflow.
Pass A decomposes observed facts, inferences, options, constraints, and missing evidence.
Pass B synthesizes the decision and records assumptions.
Do not implement the decision in this session.
Update ACTIVE.md and stop.
"""
    raise ValueError(f"Unknown role: {role}")
