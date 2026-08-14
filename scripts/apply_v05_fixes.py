from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(relative: str, content: str) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def replace_once(relative: str, old: str, new: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Expected patch anchor missing in {relative}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


replace_once(
    "src/repo_state_agent/runtime/config.py",
    '''    soft_input = _nested_nonnegative_int(
        rotation,
        "soft_input_tokens",
        runtime,
        "rotation_soft_input_tokens",
        48_000,
    )
    if hard_input and soft_input > hard_input:
        raise ValueError("runtime.rotation.soft_input_tokens cannot exceed hard_input_tokens")
''',
    '''    soft_input = _nested_nonnegative_int(
        rotation,
        "soft_input_tokens",
        runtime,
        "rotation_soft_input_tokens",
        48_000,
    )
    soft_is_explicit = (
        "soft_input_tokens" in rotation or "rotation_soft_input_tokens" in runtime
    )
    if hard_input and soft_input > hard_input and not soft_is_explicit:
        soft_input = int(hard_input * 0.8)
    if hard_input and soft_input > hard_input:
        raise ValueError("runtime.rotation.soft_input_tokens cannot exceed hard_input_tokens")
''',
)

replace_once(
    "src/repo_state_agent/cli.py",
    '''        rotation_soft_input_tokens=(
            args.rotation_soft_input_tokens
            if args.rotation_soft_input_tokens is not None
            else config.rotation_soft_input_tokens
        ),
''',
    '''        rotation_soft_input_tokens=(
            args.rotation_soft_input_tokens
            if args.rotation_soft_input_tokens is not None
            else (
                min(config.rotation_soft_input_tokens, int(args.rotate_input_tokens * 0.8))
                if args.rotate_input_tokens is not None and args.rotate_input_tokens > 0
                else config.rotation_soft_input_tokens
            )
        ),
''',
)

replace_once(
    "src/repo_state_agent/runtime/tui/model.py",
    '''        with self._lock:
            if event_type == "supervisor_started":
''',
    '''        with self._lock:
            if event_type == "context_plan":
                total = _integer(event.get("total_tokens"))
                stable = _integer(event.get("stable_tokens"))
                dynamic = _integer(event.get("dynamic_tokens"))
                budget = _integer(event.get("budget_tokens"))
                within = bool(event.get("within_budget", True))
                detail = f"stable {stable} · dynamic {dynamic} · budget {budget}"
                self._push_recent(
                    "context",
                    f"Context plan {'accepted' if within else 'requires review'} · {total} tokens",
                    detail,
                    "success" if within else "warning",
                )
                return

            if event_type in {"rotation_evaluated", "rotation_scheduled"}:
                reason = _string(event.get("reason"))
                rotate = bool(event.get("rotate"))
                fresh = _integer(event.get("fresh_input_tokens"))
                ratio_value = event.get("cache_reuse_ratio")
                ratio = (
                    f"{float(ratio_value) * 100:.0f}%"
                    if isinstance(ratio_value, int | float)
                    else "unknown"
                )
                self._next_reason = reason
                title = "Context rotation scheduled" if rotate else "Cache locality acceptable"
                detail = f"fresh {fresh} · cache reuse {ratio} · {reason}"
                self._push_recent(
                    "rotate" if rotate else "context",
                    title,
                    detail,
                    "warning" if rotate else "success",
                )
                if rotate:
                    self._current_activity = Activity(
                        "rotate", "Preparing a fresh Codex context", reason
                    )
                return

            if event_type == "supervisor_started":
''',
)

write(
    "src/repo_state_agent/templates/WORKFLOW.md",
    '''# Repository-State Workflow

## Authority

`AGENTS.md`, `ACTIVE.md`, the active task, accepted decisions, schemas, tests, and raw
evidence are durable repository authority. Conversation history is not.

## Context Plan

Use `rsaw context .` to inspect the ordered bootstrap:

```text
stable prefix → dynamic authority → bounded required reads
```

Fresh epochs read the full minimal plan. Continued epochs reread dynamic authority and
reuse stable policy only while its fingerprint is unchanged.

## Runtime

Every supervised turn closes one durable checkpoint. Verification then derives
CONTINUE, ROTATE, PAUSE, or COMPLETE. Runtime pressure may force a fresh context, but
must never weaken human, review, or scientific boundaries.

## Measurement

Track total input, cached input, fresh input, output, checkpoints, epochs, rotations,
and wall time. Prefer fresh input per successful checkpoint over cache hit rate alone.
''',
)

write(
    "docs/getting-started.md",
    '''# Getting Started

## Install

```bash
python -m pip install \
  git+https://github.com/hanklin9188/repository-state-agent-workflow.git
```

Automatic execution also requires an authenticated local Codex CLI.

## Initialize

```bash
cd /path/to/project
rsaw init .
```

Initialization creates only missing files. Customize `AGENTS.md`, `ACTIVE.md`, the
bootstrap workstream, and the first real task before autonomous execution.

## Verify and inspect

```bash
rsaw verify .
rsaw context .
rsaw status .
rsaw next .
rsaw doctor . --agent codex
```

`rsaw context` shows the stable prefix, dynamic authority, hashes, approximate tokens,
and budget status. Use `--strict` only after calibrating the repository budget.

## Preview

```bash
rsaw preview . --seconds 6
```

Preview is non-destructive and does not launch Codex.

## Run

```bash
rsaw run . --agent codex
```

Interactive terminals show the Live Runtime Console. Use `--no-tui` for plain logs.

## Upgrade safety

Do not hot-upgrade a running supervisor. Wait for a durable checkpoint or safe pause,
then update the Python package and rerun verification, context inspection, doctor, and
dry-run checks.
''',
)

write(
    "docs/runtime-evaluation.md",
    '''# Runtime Evaluation

## Question

Does repository-backed, cache-aware context lifecycle improve long-running execution
without reducing checkpoint quality or weakening governance?

## Matched conditions

Hold constant:

- repository revision and starting state;
- model/profile;
- task and permissions;
- sandbox and human-gate policy;
- validation oracle;
- hardware and external services where relevant.

Compare conditions such as chat-as-memory, always-fresh execution, bounded epochs, and
RSAW 0.5 cache-aware runtime.

## Primary metrics

1. attempted checkpoints;
2. successful checkpoints and success rate;
3. total input tokens;
4. cached input tokens;
5. fresh input tokens;
6. input tokens per successful checkpoint;
7. fresh input tokens per successful checkpoint;
8. output tokens;
9. context epochs and rotations;
10. manual relays;
11. true human gates;
12. wall time per successful checkpoint.

## Protocol discipline

Freeze policy thresholds before formal comparison. Keep the validator independent from
the runtime condition. Seal raw usage, event, checkpoint, and timing evidence before
analysis.

## Claim boundary

Implementation tests establish behavior, not causal efficiency. A successful pilot does
not establish universal gains. Report negative and neutral results.
''',
)

write(
    "docs/faq.md",
    '''# FAQ

## Does the Live Console save tokens?

No. It is local presentation. Context efficiency comes from repository-backed state,
minimal ordered reads, bounded epochs, continuation discipline, and rotation.

## Is more cached input always better?

No. Cached context is useful only while it remains relevant. RSAW balances cache reuse
against stale-context carryover and fresh-input pressure.

## What does Context Pressure mean?

It is latest-turn input relative to RSAW's configured hard rotation threshold. It is
not the model's complete context-window utilization.

## Why use both stable and dynamic fingerprints?

They let a continued thread avoid reloading unchanged policy while still refreshing
`ACTIVE.md`, the active task, and bounded evidence.

## Will 0.5 break a 0.4 config?

The flat `rotate_input_tokens` field remains supported. New nested configuration is
recommended but not mandatory.

## Should strict context budgets be enabled immediately?

No. Inspect real task plans first, calibrate the budget, then enable strict enforcement.

## Can two Codex sessions use the same repository?

Read-only inspection is possible, but only one supervisor/writer should own the active
workstream. The runtime lock prevents a second supervisor.
''',
)

write(
    "docs/company-adoption.md",
    '''# Company Adoption

## Adoption sequence

1. Start in manual repository-state mode.
2. Define stable policy, task/checkpoint contracts, and explicit human gates.
3. Run `rsaw context .` across representative tasks and calibrate budgets.
4. Pilot the Runtime Supervisor with plain logs or the Live Console.
5. Measure checkpoint quality, fresh-input cost, wall time, and intervention rate.
6. Enable strict budgets only after non-inferiority and operational review.

## Governance

RSAW complements issue trackers, CI, review, secrets management, access control, and
incident processes. It does not replace them. Company policy and authorization remain
outside model discretion.

## Recommended rollout metrics

- successful checkpoints;
- fresh input per checkpoint;
- cache reuse ratio with task relevance review;
- rotations and reason codes;
- manual relays and human gates;
- failure recovery and evidence completeness;
- wall time per successful checkpoint.

## Rollback

Pin exact package revisions. Preserve the previous installation source and command.
Never hot-upgrade a supervisor that already owns a repository.
''',
)

write(
    "PUBLISH.md",
    '''# Publishing RSAW

## Release validation

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest -q
rsaw verify .
rsaw context . --strict
rsaw footprint . --max-tokens 15000
rsaw run . --dry-run
rsaw report . --json
python scripts/check_markdown_links.py .
```

Run `rsaw preview .` manually in a real terminal before publishing a UI release.

## Repository presentation

- Description: repository-backed workstreams with cache-aware context planning,
  automatic Codex rotation, and a live terminal runtime console.
- Keep the architecture, context lifecycle, and terminal dashboard visuals near the
  top of the README.
- Update `REPOSITORY_METADATA.json`, `CITATION.cff`, changelog, roadmap, and version
  together.

## Claim discipline

Do not describe approximate context counts as provider billing. Do not claim universal
token or quality improvement before matched prospective evidence.
''',
)

scaffold_test = ROOT / "tests/test_scaffold.py"
if scaffold_test.is_file():
    text = scaffold_test.read_text(encoding="utf-8")
    text = text.replace("len(created) == 7", "len(created) == 8")
    text = text.replace("len(skipped) == 7", "len(skipped) == 8")
    scaffold_test.write_text(text, encoding="utf-8")

for relative in (
    "scripts/apply_v05_core.py",
    "scripts/apply_v05_docs.py",
    "scripts/apply_v05_fixes.py",
    ".github/workflows/apply-v05-upgrade.yml",
):
    (ROOT / relative).unlink(missing_ok=True)

print("RSAW 0.5 compatibility, TUI, and supporting docs staged")
