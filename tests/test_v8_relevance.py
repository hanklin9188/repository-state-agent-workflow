from __future__ import annotations

import json
import subprocess
from pathlib import Path

from repo_state_agent.parsing import parse_active
from repo_state_agent.runtime.relevance import (
    RelevanceConfig,
    build_focus_bundle,
    build_repository_index,
    fixture_context_metrics,
    migrate_v8,
)


def _repo(root: Path) -> None:
    subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    (root / "docs/tasks").mkdir(parents=True)
    (root / "docs/workstreams").mkdir(parents=True)
    (root / "src").mkdir()
    (root / "tests").mkdir(exist_ok=True)
    (root / ".rsaw").mkdir()
    (root / "AGENTS.md").write_text("# Policy\nRepository state is authoritative.\n")
    (root / "docs/workstreams/W.md").write_text("# W\n")
    (root / "docs/tasks/FIX.md").write_text(
        """# Fix profiler duration conversion

Repair `src/observer.py` so `normalize_elapsed_us` supports callable and numeric values.
Add a rejecting regression in `tests/test_observer.py`.

## Allowed Writes
- src/observer.py
- tests/test_observer.py

## Validation
- `python -m pytest -q tests/test_observer.py`
""",
        encoding="utf-8",
    )
    (root / "ACTIVE.md").write_text(
        """# Active Handoff

## Workstream
ID: W
Spec: docs/workstreams/W.md

## Context Epoch
ID: E-1
Role: Builder

## Active Task
ID: PROFILER-COMPATIBILITY-FIX
Spec: docs/tasks/FIX.md

## Required Reads
- AGENTS.md
- ACTIVE.md
- docs/tasks/FIX.md

## Human Gate
None.

## Next Exact Action
Implement normalize_elapsed_us and its rejecting test.

## Stop Condition
Focused validation passes.

## Continuation Gate
Decision: CONTINUE_ALLOWED
Reason: same role

## Next Task
ID: PROFILER-COMPATIBILITY-FIX
Spec: docs/tasks/FIX.md

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
                "schema_version": 5,
                "runtime": {
                    "v6": {"enabled": True},
                    "relevance": {
                        "enabled": True,
                        "mapTokens": 600,
                        "focusTokens": 1_400,
                        "maxSnippets": 5,
                        "candidateLimit": 16,
                        "snippetLines": 60,
                        "maxFileBytes": 200000,
                        "maxIndexFiles": 1000,
                    },
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "src/observer.py").write_text(
        """from __future__ import annotations


def normalize_elapsed_us(value):
    \"\"\"Return profiler duration as a float.\"\"\"
    return float(value)


class TorchDiagnosticExecutor:
    def activity_rows(self, events):
        return [normalize_elapsed_us(event.time_range.elapsed_us) for event in events]
""",
        encoding="utf-8",
    )
    (root / "tests/test_observer.py").write_text(
        """from src.observer import normalize_elapsed_us


def test_callable_elapsed_us():
    assert normalize_elapsed_us(lambda: 2.5) == 2.5
""",
        encoding="utf-8",
    )
    for index in range(18):
        body = [
            f"def unrelated_{index}_{line}(value):\n    return value + {line}\n"
            for line in range(60)
        ]
        (root / "src" / f"unrelated_{index}.py").write_text("\n".join(body), encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd=root,
        check=True,
    )


def test_focus_selects_target_and_reduces_fixture_context(tmp_path: Path) -> None:
    _repo(tmp_path)
    state = parse_active(tmp_path)
    bundle = build_focus_bundle(tmp_path, state, force_index=True)
    metrics = fixture_context_metrics(tmp_path, state)

    assert bundle.enabled
    assert "src/observer.py" in bundle.selected_files
    assert "normalize_elapsed_us" in bundle.prompt_block()
    assert metrics["reductionRatio"] >= 0.70
    assert metrics["focusTokens"] < metrics["baselineTokens"]


def test_index_cache_reuses_unchanged_files_and_reparses_one_change(tmp_path: Path) -> None:
    _repo(tmp_path)
    config = RelevanceConfig.from_root(tmp_path)

    first = build_repository_index(tmp_path, config=config)
    assert first.cache_misses == first.indexed_files
    assert first.cache_hits == 0

    second = build_repository_index(tmp_path, config=config)
    assert second.cache_hits == second.indexed_files
    assert second.cache_misses == 0

    target = tmp_path / "src/observer.py"
    target.write_text(target.read_text() + "\n# changed\n", encoding="utf-8")
    third = build_repository_index(tmp_path, config=config)
    assert third.cache_misses == 1
    assert third.cache_hits == third.indexed_files - 1


def test_focus_is_deterministic_and_respects_component_budgets(tmp_path: Path) -> None:
    _repo(tmp_path)
    state = parse_active(tmp_path)

    first = build_focus_bundle(tmp_path, state, force_index=True)
    second = build_focus_bundle(tmp_path, state)

    assert first.sha256 == second.sha256
    assert first.map_tokens <= 600
    assert first.snippet_tokens <= 1_400
    assert len(first.snippets) <= 5


def test_required_reads_are_not_duplicated_as_focus_snippets(tmp_path: Path) -> None:
    _repo(tmp_path)
    state = parse_active(tmp_path)
    bundle = build_focus_bundle(tmp_path, state, force_index=True)

    assert "ACTIVE.md" not in bundle.selected_files
    assert "AGENTS.md" not in bundle.selected_files
    assert "docs/tasks/FIX.md" not in bundle.selected_files


def test_sensitive_runtime_evidence_and_artifacts_are_not_indexed(tmp_path: Path) -> None:
    _repo(tmp_path)
    (tmp_path / ".env").write_text("TOKEN=secret\n")
    (tmp_path / ".rsaw/runtime/run").mkdir(parents=True)
    (tmp_path / ".rsaw/runtime/run/log.jsonl").write_text("secret\n")
    (tmp_path / ".rsaw/state/evidence").mkdir(parents=True)
    (tmp_path / ".rsaw/state/evidence/EV.json").write_text("secret\n")
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "artifacts/raw.json").write_text("secret\n")

    index = build_repository_index(tmp_path, force=True)

    assert ".env" not in index.files
    assert not any(path.startswith(".rsaw/runtime/") for path in index.files)
    assert not any(path.startswith(".rsaw/state/evidence/") for path in index.files)
    assert not any(path.startswith("artifacts/") for path in index.files)


def test_disabled_relevance_returns_empty_bundle(tmp_path: Path) -> None:
    _repo(tmp_path)
    config = json.loads((tmp_path / ".rsaw/config.json").read_text())
    config["runtime"]["relevance"]["enabled"] = False
    (tmp_path / ".rsaw/config.json").write_text(json.dumps(config) + "\n")

    bundle = build_focus_bundle(tmp_path, parse_active(tmp_path))

    assert not bundle.enabled
    assert bundle.total_tokens == 0
    assert bundle.selected_files == ()


def test_migrate_v8_preserves_active_and_is_idempotent(tmp_path: Path) -> None:
    _repo(tmp_path)
    config_path = tmp_path / ".rsaw/config.json"
    config = json.loads(config_path.read_text())
    config["schema_version"] = 4
    config["runtime"].pop("relevance")
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    active_before = (tmp_path / "ACTIVE.md").read_bytes()

    plan = migrate_v8(tmp_path, apply=False)
    assert plan["target"] == "0.8"
    assert not plan["apply"]

    applied = migrate_v8(tmp_path, apply=True)
    assert applied["status"] == "MIGRATED"
    assert (tmp_path / "ACTIVE.md").read_bytes() == active_before
    migrated = json.loads(config_path.read_text())
    assert migrated["schema_version"] == 5
    assert migrated["runtime"]["relevance"]["enabled"] is True
    assert (tmp_path / ".rsaw/config.v071.backup.json").is_file()

    again = migrate_v8(tmp_path, apply=True)
    assert again["status"] == "ALREADY_CURRENT"
