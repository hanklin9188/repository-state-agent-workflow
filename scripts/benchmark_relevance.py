from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from repo_state_agent.parsing import parse_active
from repo_state_agent.runtime.relevance import fixture_context_metrics


def build_fixture(root: Path) -> None:
    subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    (root / "docs/tasks").mkdir(parents=True)
    (root / "docs/workstreams").mkdir(parents=True)
    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / ".rsaw").mkdir()
    (root / "AGENTS.md").write_text("# Policy\n")
    (root / "docs/workstreams/W.md").write_text("# W\n")
    (root / "docs/tasks/T.md").write_text(
        """# GPU observer compatibility repair

Repair `src/gpu_observer.py` function `normalize_elapsed_us` and the rejecting
regression in `tests/test_gpu_observer.py`. Preserve the process-inventory gate.

## Allowed Writes
- src/gpu_observer.py
- tests/test_gpu_observer.py

## Validation
- `python -m pytest -q tests/test_gpu_observer.py`
"""
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
ID: GPU-OBSERVER-COMPATIBILITY
Spec: docs/tasks/T.md

## Required Reads
- AGENTS.md
- ACTIVE.md
- docs/tasks/T.md

## Human Gate
None.

## Next Exact Action
Repair normalize_elapsed_us and its rejecting regression.

## Stop Condition
Focused validation passes.

## Continuation Gate
Decision: CONTINUE_ALLOWED
Reason: same role

## Next Task
ID: GPU-OBSERVER-COMPATIBILITY
Spec: docs/tasks/T.md

## Next Session Role
Builder

## Recommended Reasoning
Medium
"""
    )
    (root / ".rsaw/config.json").write_text(
        json.dumps(
            {
                "schema_version": 5,
                "runtime": {
                    "v6": {"enabled": True},
                    "relevance": {
                        "enabled": True,
                        "mapTokens": 800,
                        "focusTokens": 1800,
                        "maxSnippets": 6,
                        "candidateLimit": 24,
                        "snippetLines": 72,
                    },
                },
            }
        )
        + "\n"
    )
    (root / "src/gpu_observer.py").write_text(
        """def normalize_elapsed_us(value):
    if callable(value):
        value = value()
    return float(value)


class GpuObserver:
    def activity_rows(self, events):
        return [normalize_elapsed_us(event.time_range.elapsed_us) for event in events]
"""
    )
    (root / "tests/test_gpu_observer.py").write_text(
        """from src.gpu_observer import normalize_elapsed_us


def test_callable_elapsed_us():
    assert normalize_elapsed_us(lambda: 3.5) == 3.5


def test_numeric_elapsed_us():
    assert normalize_elapsed_us(4) == 4.0
"""
    )
    (root / "src/process_inventory.py").write_text(
        "def prohibited_gpu_processes(processes):\n"
        "    return [p for p in processes if p.prohibited]\n"
    )
    for index in range(36):
        blocks = [
            f"def unrelated_{index}_{line}(value):\n    return value + {line}\n"
            for line in range(80)
        ]
        (root / "src" / f"unrelated_{index}.py").write_text("\n".join(blocks))
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Benchmark",
            "-c",
            "user.email=benchmark@example.com",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd=root,
        check=True,
    )


def run() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="rsaw-v080-benchmark-") as directory:
        root = Path(directory)
        build_fixture(root)
        state = parse_active(root)
        first = fixture_context_metrics(root, state, force_index=True)
        second = fixture_context_metrics(root, state)
        selected = set(first["selectedFiles"])
        target_coverage = {
            "implementation": "src/gpu_observer.py" in selected,
            "rejectingTest": "tests/test_gpu_observer.py" in selected,
        }
        result = {
            "schemaVersion": "rsaw.relevance-benchmark.v1",
            "fixture": "gpu-observer-compatibility-with-36-distractor-modules",
            "baselineTokens": first["baselineTokens"],
            "focusTokens": first["focusTokens"],
            "reductionRatio": round(float(first["reductionRatio"]), 6),
            "targetCoverage": target_coverage,
            "selectedFiles": first["selectedFiles"],
            "firstBuild": {
                "cacheHits": first["cacheHits"],
                "cacheMisses": first["cacheMisses"],
            },
            "secondBuild": {
                "cacheHits": second["cacheHits"],
                "cacheMisses": second["cacheMisses"],
            },
        }
        result["pass"] = bool(
            result["reductionRatio"] >= 0.70
            and all(target_coverage.values())
            and int(second["cacheMisses"]) == 0
            and int(second["cacheHits"]) == int(second["indexedFiles"])
        )
        return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    result = run()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    print(text, end="")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
