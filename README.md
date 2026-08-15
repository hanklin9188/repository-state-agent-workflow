<p align="center">
  <img src="docs/assets/banner-v07.svg" alt="RSAW v0.7 — Repository Context Runtime" width="100%" />
</p>

<h1 align="center">Repository-State Agent Workflow</h1>

<p align="center">
  <strong>Keep project truth in the repository. Give the agent only the context it needs. Commit progress transactionally.</strong>
</p>

<p align="center">
  <img alt="Python 3.10–3.13" src="https://img.shields.io/badge/Python-3.10%E2%80%933.13-3776AB?logo=python&logoColor=white" />
  <img alt="Version 0.7.1" src="https://img.shields.io/badge/RSAW-0.7.1-14b8a6" />
  <img alt="License MIT" src="https://img.shields.io/badge/License-MIT-22c55e" />
  <img alt="Codex adapter" src="https://img.shields.io/badge/Adapter-Codex-6366f1" />
</p>

<p align="center">
  <a href="README.zh-TW.md">繁體中文</a> ·
  <a href="docs/edgeflow-v071-deployment.md">EdgeFlow deployment</a> ·
  <a href="docs/releases/v071-gpu-sandbox-boundary.md">v0.7 hardening</a> ·
  <a href="CHANGELOG.md">Changelog</a>
</p>

---

## What RSAW is

RSAW is a repository-backed runtime that supervises long-lived coding and research agents.

It does **not** try to replace Codex or build another chat interface. Codex remains the semantic worker. RSAW owns the surrounding runtime concerns that should be deterministic:

- durable project state and checksummed checkpoints;
- minimal context compilation;
- evidence and validation binding;
- `CONTINUE`, `COMPACT`, `ROTATE`, `PAUSE`, and `COMPLETE` lifecycle decisions;
- Human Gate and sandbox controls;
- live tool/context budgets;
- recovery after interruption or a failed state transition.

The core rule is simple:

> **The model may forget. The repository must not.**

---

## Start in 60 seconds

### Install

```bash
python -m pip install --upgrade \
  "git+https://github.com/hanklin9188/repository-state-agent-workflow.git@v0.7.1"
```

### Existing RSAW repository

```bash
rsaw upgrade . --apply
rsaw preflight .
rsaw start .
```

### New repository

```bash
rsaw init .
rsaw preflight .
rsaw start .
```

`rsaw start .` is the normal daily command. It runs preflight, resolves the configured Codex binary and sandbox profile, then opens the Live Runtime Console.

```text
start
  ├── verify repository state
  ├── verify Codex + authentication
  ├── resolve task sandbox profile
  ├── load durable checkpoint
  └── run supervised Codex with live budgets
```

---

## The operator experience

<p align="center">
  <img src="docs/assets/live-terminal-dashboard-v07.svg" alt="RSAW v0.7 Live Runtime Console" width="96%" />
</p>

The terminal shows observable runtime state, not hidden reasoning:

| Panel | What it answers |
|---|---|
| **NOW** | Which task, role, mode, and durable checkpoint are active? |
| **LIFECYCLE** | Will RSAW continue, compact, rotate, pause, or complete? |
| **WORKING MEMORY** | How large are the Context Envelope and Semantic Capsule? |
| **EFFICIENCY GUARD** | How much provider input and tool output is accumulating? |
| **RECENT** | Which durable runtime events just occurred? |

A new terminal no longer starts visually at checkpoint zero when durable checkpoints already exist. Expected `PAUSED`, `COMPLETE`, `LIMIT_REACHED`, and `DRY_RUN` states exit cleanly in both TUI and non-TUI operator use instead of appearing as VS Code terminal failures. `--strict-exit-codes` preserves machine-oriented codes.

---

## Why v0.7 exists

v0.7 was derived from a real EdgeFlow adoption, not a synthetic feature wishlist. The v0.6 run exposed several runtime contracts that looked correct in unit tests but failed under real work:

| Real failure | v0.7 behavior |
|---|---|
| A stale user-local `rsaw` shadowed the active Conda environment | `preflight` reports launcher/Python mismatch; module execution remains available |
| Human Gate state conflicted with continuation prose | gate operations are atomic, role-aware, verified, and audited |
| Source paths were rejected as unknown evidence IDs | evidence authority is now explicitly Supervisor-owned |
| Codex returned `task_id` instead of `id` | task references accept canonical camelCase and snake_case forms |
| TUI showed checkpoint 0 after restart | the dashboard loads the repository-global durable checkpoint |
| ACTIVE updates accumulated blank lines past the 140-line limit | canonical rendering is idempotent and budgeted before commit |
| Checkpoint files were written before post-advance verification failed | the whole authority transition is transactional and rolls back |
| GPU-visible work required repeating a long CLI command | task sandbox profiles persist in repository configuration |
| A 1–2k compiled envelope still grew into a very large tool-driven context | live per-turn tool and output budgets stop runaway rediscovery |
| started/completed command events inflated telemetry | event accounting is deduplicated by tool identity |

The detailed release gate is documented in [v0.7 EdgeFlow-derived hardening](docs/releases/v071-gpu-sandbox-boundary.md).

---

## Architecture

<p align="center">
  <img src="docs/assets/runtime-architecture-v07.svg" alt="RSAW v0.7 transactional architecture" width="96%" />
</p>

```text
Repository Authority
        ↓
Context Compiler
        ↓
Replaceable Agent Worker
        ↓
Typed CheckpointResult
        ↓
Deterministic Gate
        ↓
Transactional Commit
        ↓
Token / Tool Governor
        ↓
CONTINUE · COMPACT · ROTATE · PAUSE · COMPLETE
```

### The model does semantic work

The worker reads the compiled task context, edits code, runs validation, and returns one typed `rsaw.checkpoint-result.v1` object.

### The Supervisor does deterministic work

RSAW verifies the real diff, validation commands, artifacts, allowed-write scope, evidence, next task, and lifecycle transition. The model does not edit `ACTIVE.md` or invoke an advancement script.

### State advancement is transactional

Before committing a checkpoint, RSAW:

1. renders and validates the proposed `ACTIVE.md`;
2. snapshots all authority files;
3. writes the capsule, checkpoint, checksum, review manifest, and active pointer;
4. verifies the repository again;
5. rolls the whole transition back if any post-write invariant fails.

A failed transition must not leave a half-advanced workstream.

---

## Lifecycle semantics

<p align="center">
  <img src="docs/assets/lifecycle-v07.svg" alt="RSAW lifecycle actions" width="96%" />
</p>

| Action | Meaning |
|---|---|
| `CONTINUE` | Reuse the current context for the same role and coherent objective. |
| `COMPACT` | Preserve semantic working memory while replacing an expensive hot context. |
| `ROTATE` | Create a fresh independent context for a role/objective boundary. |
| `PAUSE` | Persist a real human, external, privilege, or safety gate. |
| `COMPLETE` | Close only after the durable stop condition is satisfied. |

```text
Checkpoint = durability boundary
Context epoch = cognitive boundary
```

A checkpoint does not automatically force a fresh context.

---

## Bounded working context

RSAW controls two different sources of context growth.

### 1. Context Compiler

The compiler produces a sealed Context Envelope from:

- stable governance;
- the exact task contract;
- bounded Semantic Capsule state;
- current delta;
- exact evidence only when required;
- references for large historical material.

Default envelope targets are 6k tokens with a 12k hard ceiling.

### 2. Live tool budget

A small initial prompt is not enough if the agent subsequently performs broad discovery and returns huge tool outputs. v0.7 therefore enforces a per-turn budget:

```json
{
  "maxToolCallsPerTurn": 32,
  "maxToolOutputTokens": 50000,
  "maxSingleToolOutputTokens": 20000,
  "maxBroadDiscoveryCommands": 2,
  "enforce": true
}
```

When exceeded, RSAW requests a process stop and returns a durable `PAUSED` state with a precise `TOOL_BUDGET_EXCEEDED:*` reason. Budgets reset for every agent turn.

These defaults are engineering guardrails, not universal optima.

---

## Daily commands

| Goal | Command |
|---|---|
| Start normal supervised work | `rsaw start .` |
| Check everything without starting | `rsaw preflight .` |
| Show active repository state | `rsaw status .` |
| Inspect runtime efficiency | `rsaw report .` |
| Preview compiled context | `rsaw compile . --mode FRESH` |
| Normalize ACTIVE formatting | `rsaw state normalize .` |
| Preview the terminal UI | `rsaw preview .` |

The full CLI remains available through `rsaw --help` and `python -m repo_state_agent --help`.

---

## Human Gates without hand-editing ACTIVE.md

Inspect:

```bash
rsaw gate show . --json
```

Clear only after the prerequisite is truly satisfied:

```bash
rsaw gate clear . \
  --reason "external prerequisite restored and verified" \
  --yes
```

RSAW records an operator-action artifact, validates the new state, and chooses the correct continuation policy:

- same role → `CONTINUE_ALLOWED`;
- role boundary → `ROTATE_REQUIRED`.

A failed gate update restores the previous `ACTIVE.md`.

---

## Task-specific sandbox profiles

The default remains `workspace-write`.

A reviewed task that genuinely requires direct GPU/NVML access can receive a persistent task-scoped profile:

```bash
rsaw sandbox set . \
  --task current \
  --mode danger-full-access \
  --reason "reviewed GPU/NVML boundary" \
  --yes

rsaw preflight .
rsaw start .
```

Inspect or remove it:

```bash
rsaw sandbox show . --json
rsaw sandbox clear . --task current --reason "boundary closed" --yes
```

The override is keyed to the task ID and is resolved again before every Codex turn. A sandbox-class change forces a fresh context boundary, so a broader Runner profile cannot silently continue into a later Analyst or Builder task. Set and clear operations are content-bound operator actions and roll back if the audit cannot be written. An explicit `--sandbox` value is also scoped to the task active when the run starts; after a task transition, RSAW reverts to the next task's own override or the repository default.

---

## Host capability is not worker capability

A GPU/NVML failure inside `workspace-write` does not by itself prove that WSL, the driver, or the host GPU is unavailable. Diagnose the two boundaries separately:

```text
host visibility  ≠  Codex worker-sandbox visibility
```

Capability smoke is workflow infrastructure evidence only. It cannot authorize a formal retry, consume or replace an experiment nonce, modify sealed evidence, or become a scientific result. See the [EdgeFlow GPU sandbox incident](docs/incidents/2026-08-15-edgeflow-gpu-sandbox.md).

---

## Repository memory model

| Level | Contents |
|---|---|
| **Cold** | Git history, task contracts, checksummed checkpoints, evidence handles |
| **Warm** | Semantic Capsule: facts, decisions, exclusions, risks, validation, next action |
| **Hot** | Current model context and tool results for one coherent epoch |

The repository is authoritative. The TUI, chat transcript, and model memory are not.

---

## Installation and migration

### Exact release install

```bash
python -m pip install --upgrade \
  "git+https://github.com/hanklin9188/repository-state-agent-workflow.git@v0.7.1"
```

### Upgrade an existing repository

```bash
rsaw upgrade . --json
rsaw upgrade . --apply
rsaw state normalize .
rsaw preflight .
rsaw start .
```

Migration preserves `ACTIVE.md` and writes a v0.6 configuration backup. See the complete [EdgeFlow v0.7 deployment guide](docs/edgeflow-v071-deployment.md) for process/lock checks, sandbox configuration, Human Gate handling, validation, and rollback.

---

## Safety boundaries

RSAW does not make an unsafe task safe merely by supervising it.

- A Human Gate remains authoritative until explicitly cleared.
- A one-shot experiment remains one-shot even if a checkpoint fails.
- `danger-full-access` must be task-scoped and separately justified.
- Failed/invalid/diagnostic artifacts do not become formal evidence.
- A token win is not accepted if matched semantic success regresses.
- UI rendering never owns lifecycle state.

---

## Evidence and claim boundary

v0.7 is validated for implementation behavior, transactional state safety, migration, packaging, operator controls, tool-budget enforcement, and synthetic lifecycle coverage.

It does **not** yet claim a universal reduction in provider tokens, wall time, or failure rate. Those claims require matched prospective evaluation on real workstreams.

The primary empirical quantities are:

```text
successful checkpoints
success rate
total / cached / fresh input per success
model and tool calls per success
tool-output and repeated-input traffic
compactions and rotations
manual relay and true human gates
wall time per success
recovery rediscovery commands
```

---

## Documentation

- [EdgeFlow v0.7 deployment](docs/edgeflow-v071-deployment.md)
- [v0.7 release hardening](docs/releases/v071-gpu-sandbox-boundary.md)
- [Architecture](docs/architecture.md)
- [Concepts](docs/concepts.md)
- [Adoption guide](docs/adoption-guide.md)
- [Codex adapter](docs/codex-adapter.md)
- [Anti-patterns](docs/anti-patterns.md)
- [Evaluation methodology](docs/context-epoch-evaluation.md)
- [Changelog](CHANGELOG.md)
- [Roadmap](ROADMAP.md)

---

## Development

```bash
python -m pip install -e '.[dev]'
ruff format --check .
ruff check .
pytest -q
rsaw verify .
rsaw compile . --mode FRESH --json
rsaw acceptance . --horizon all --json
python scripts/check_markdown_links.py .
python -m build
```

CI validates Python 3.10, 3.12, and 3.13, plus a clean isolated wheel installation.

## License

MIT
