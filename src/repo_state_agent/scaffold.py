from __future__ import annotations

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
    for relative in (
        "docs/handoffs/archive",
        "docs/checkpoints",
        "docs/decisions",
        ".rsaw/state/checkpoints",
        ".rsaw/state/capsules",
        ".rsaw/state/evidence",
        ".rsaw/state/envelopes",
        ".rsaw/state/reviews",
    ):
        (root / relative).mkdir(parents=True, exist_ok=True)
    return created, skipped
