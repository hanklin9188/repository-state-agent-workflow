from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(relative: str, content: str) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


write(
    "README.md",
    '''<p align="center">
  <img src="docs/assets/banner.svg" alt="Repository-State Agent Workflow banner" width="100%" />
</p>

<h1 align="center">Repository-State Agent Workflow</h1>

<p align="center">
  <strong>Persistent workstreams. Cache-aware contexts. Live operator visibility.</strong>
</p>

<p align="center">
  RSAW keeps durable project memory in the repository, builds an explicit minimal
  context plan, reuses a Codex thread only while cache locality remains useful,
  rotates automatically at real boundaries, and shows the entire run in a clear
  terminal-native console.
</p>

<p align="center">
  <a href="https://github.com/hanklin9188/repository-state-agent-workflow/actions/workflows/ci.yml"><img src="https://github.com/hanklin9188/repository-state-agent-workflow/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-0f766e" alt="MIT License" /></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%2B-2563eb" alt="Python 3.10+" /></a>
  <img src="https://img.shields.io/badge/version-0.5.0-7c3aed" alt="Version 0.5.0" />
  <img src="https://img.shields.io/badge/runtime-Codex_CLI-111827" alt="Codex CLI runtime" />
  <img src="https://img.shields.io/badge/context-cache_aware-0891b2" alt="Cache-aware context" />
  <img src="https://img.shields.io/badge/UI-live_terminal-0f766e" alt="Live terminal UI" />
</p>

<p align="center">
  <a href="#two-minute-start">Start</a> ·
  <a href="#the-operating-model">Operating model</a> ·
  <a href="#cache-aware-context-planning">Context planning</a> ·
  <a href="#deterministic-rotation-policy">Rotation</a> ·
  <a href="#live-runtime-console">Live console</a> ·
  <a href="#evidence-and-claim-boundaries">Evidence</a> ·
  <a href="README.zh-TW.md">繁體中文</a>
</p>

---

## What RSAW is

**RSAW is a repository-first operating model and runtime supervisor for long-running
coding and research agents.**

The repository stores durable memory. Agent contexts are bounded, replaceable workers.
For every verified checkpoint, RSAW deterministically chooses one action:

- **CONTINUE** — reuse the current thread for tightly coupled work;
- **ROTATE** — start a fresh context while the workstream keeps running;
- **PAUSE** — stop at a genuine human or external gate;
- **COMPLETE** — close the workstream.

Version 0.5 adds a cache-aware context planner and a deterministic rotation policy on
top of the 0.4 Live Runtime Console.

> **The workstream persists. Context is planned, measured, and replaceable.**

<p align="center">
  <img src="docs/assets/runtime-architecture-v05.svg" alt="RSAW 0.5 architecture" width="100%" />
</p>

---

## The problem

A long agent chat quietly becomes an accidental project database:

```text
old source snapshots
+ failed attempts
+ obsolete decisions
+ raw command output
+ completed tasks
+ current work
```

Keeping everything forever increases stale-context traffic. Starting fresh after every
step avoids staleness but repeatedly rereads policy, reconstructs the repository, and
throws away useful prefix/cache locality.

RSAW separates four lifetimes:

| Layer | Typical lifetime | Responsibility |
|---|---:|---|
| `AGENTS.md` | months | stable policy, authority, safety |
| Workstream | days–weeks | long-range state machine |
| Task checkpoint | hours–days | one durable, verifiable unit |
| Context epoch | bounded | tightly coupled model turns |

The optimization target is not “maximize cached tokens” or “always start fresh.” It is:

```text
useful cache reuse
+ low stale-context carryover
+ small fresh bootstrap after rotation
+ verified progress per token
```

---

## Two-minute start

### 1. Install

```bash
python -m pip install \
  git+https://github.com/hanklin9188/repository-state-agent-workflow.git
```

Automatic mode also requires an authenticated local Codex CLI.

### 2. Initialize a repository

```bash
cd /path/to/your-project
rsaw init .
```

Initialization is additive. Existing `AGENTS.md`, `ACTIVE.md`, task files, and project
logic are not overwritten unless `--force` is explicit.

### 3. Verify authority and inspect the context plan

```bash
rsaw verify .
rsaw context .
rsaw doctor . --agent codex
rsaw status .
```

Use a budget gate when the repository has adopted a reviewed budget:

```bash
rsaw context . --strict
```

### 4. Preview the operator UI without launching Codex

```bash
rsaw preview . --seconds 6
```

### 5. Run the workstream

```bash
rsaw run . --agent codex
```

Interactive terminals, including the VS Code Integrated Terminal, receive the Live
Runtime Console. CI, redirected output, JSON mode, quiet mode, and non-TTY execution
fall back to plain logs.

```bash
rsaw run . --agent codex --no-tui   # explicit plain output
rsaw run . --agent codex --tui      # force the dashboard
```

---

## The operating model

```mermaid
flowchart LR
    A[Repository authority] --> P[Context planner]
    P --> S[RSAW supervisor]
    S --> C[Codex bounded turn]
    C --> E[Durable checkpoint]
    E --> V[Verification]
    V --> D{Next action}
    D -->|CONTINUE| C
    D -->|ROTATE| P
    D -->|PAUSE| H[Human or external gate]
    D -->|COMPLETE| X[Terminal summary]
    C -. structured events .-> U[Live Runtime Console]
    S -. lifecycle + token telemetry .-> U
```

The planner and UI are observers/supporting layers. Repository verification and the
continuation state machine remain authoritative.

---

## Cache-aware context planning

`rsaw context .` builds a deterministic manifest from repository authority:

1. stable prefix — normally `AGENTS.md` and optional stable workstream authority;
2. dynamic authority — `ACTIVE.md` and the active task;
3. bounded required reads — only explicit files, deduplicated and repository-local.

<p align="center">
  <img src="docs/assets/context-lifecycle.svg" alt="RSAW cache-aware context lifecycle" width="100%" />
</p>

Each document records:

- repository-relative path;
- category;
- bytes and approximate tokens;
- SHA-256 content hash.

The plan exposes separate stable and dynamic fingerprints. A continued thread is told
to reread dynamic authority but not reload the stable prefix unless its fingerprint
changed. A fresh epoch receives the full ordered bootstrap.

Default planning controls:

```json
{
  "runtime": {
    "context": {
      "bootstrap_token_budget": 15000,
      "max_files": 12,
      "max_file_bytes": 262144,
      "include_workstream_spec": false,
      "enforce_budget": false
    }
  }
}
```

Budget enforcement is opt-in for compatibility. Inspection is always available.
See [Context Planning](docs/context-planning.md).

---

## Deterministic rotation policy

RSAW preserves mandatory role/scientific boundaries, then evaluates runtime pressure
without asking a model to decide its own context lifetime.

Rotation reasons include:

| Reason | Meaning |
|---|---|
| `MAX_TURNS_PER_RUNTIME_EPOCH` | bounded turn count reached |
| `HARD_INPUT_TOKEN_PRESSURE` | latest input reached the hard threshold |
| `FRESH_INPUT_TOKEN_PRESSURE` | uncached/fresh input exceeded its budget |
| `LOW_CACHE_REUSE_AT_SOFT_LIMIT` | input crossed the soft threshold while reuse quality was poor |
| role/scientific boundary | repository state requires independence |

```json
{
  "runtime": {
    "rotation": {
      "soft_input_tokens": 48000,
      "hard_input_tokens": 60000,
      "max_fresh_input_tokens": 18000,
      "min_cache_reuse_ratio": 0.5
    }
  }
}
```

The policy uses provider-emitted usage only. It does not claim to measure the model's
complete context window. See [Cache-Aware Rotation](docs/cache-aware-rotation.md).

---

## Live Runtime Console

<p align="center">
  <img src="docs/assets/live-terminal-dashboard.svg" alt="RSAW Live Runtime Console" width="100%" />
</p>

The console answers five operator questions:

1. What is happening now?
2. How far has the current task advanced?
3. What will RSAW do next?
4. Is context/cache pressure healthy?
5. Does a human need to intervene?

| Area | Meaning |
|---|---|
| **NOW** | observable Codex file, command, tool, and validation activity |
| **PROGRESS** | workstream, task, role, epoch, checkpoint, next action |
| **CONTEXT** | hard/soft pressure, cache reuse, fresh-input pressure |
| **TOKEN COST** | input, cached, fresh, output, and per-checkpoint efficiency |
| **RECENT** | high-value events rather than raw JSONL |
| **FOOTER** | durable state, gate, runtime, and terminal status |

The UI never displays hidden chain-of-thought. Rendering failures are isolated and
cannot alter execution or lifecycle decisions. See [Live Terminal UI](docs/live-terminal-ui.md).

---

## Context and token metrics

The Codex adapter records provider-emitted:

- input tokens;
- cached input tokens;
- cache-write input tokens when provided;
- output tokens;
- reasoning-output tokens.

RSAW derives:

```text
fresh input = max(0, input - cached input)
cache reuse ratio = cached input / input
input per checkpoint = total input / accepted checkpoints
fresh input per checkpoint = fresh input / accepted checkpoints
```

Inspect the active plan and completed runs:

```bash
rsaw context . --json
rsaw report .
rsaw report . --json
```

The dashboard and reports are local observability. They do not add dashboard text to
model prompts or create extra model turns.

> **More observability for the human; less unnecessary context for the model.**

---

## Runtime safety

Automatic continuation does not weaken governance:

- verification runs before and after every supervised turn;
- successful turns must advance `ACTIVE.md`;
- single-supervisor locking prevents concurrent workstream ownership;
- human gates never infer approval;
- failed agent or formal runs are not silently retried;
- role and scientific boundaries stay fresh;
- turn, transition, context, and total-token limits bound execution;
- runtime logs remain ignored by default.

---

## CLI reference

| Command | Purpose |
|---|---|
| `rsaw init .` | add missing repository-state scaffolding |
| `rsaw verify .` | validate active authority and references |
| `rsaw context .` | inspect ordered context, fingerprints, and budget |
| `rsaw status .` | show active workstream and derived action |
| `rsaw next .` | derive CONTINUE / ROTATE / PAUSE / COMPLETE |
| `rsaw prompt .` | render a minimal manual-mode prompt |
| `rsaw doctor . --agent codex` | verify the Codex adapter |
| `rsaw preview .` | preview the Live Console without an agent |
| `rsaw run . --agent codex` | supervise the workstream |
| `rsaw report .` | report context and checkpoint efficiency |

---

## Configuration

The complete `.rsaw/config.json` remains intentionally small. The 0.4 flat
`rotate_input_tokens` field remains accepted for backward compatibility, while 0.5
uses explicit `rotation` and `context` sections in new repositories.

See [Migration 0.4 → 0.5](docs/migration-v4-to-v5.md).

---

## Evidence and claim boundaries

Documented evidence currently includes:

- cross-version CI and focused runtime/TUI tests;
- deterministic context-plan and rotation-policy tests;
- a Desk Code Agent bootstrap-footprint case study;
- an EdgeFlow RSAW 0.1/0.2 retrospective matched replay;
- prospective runtime telemetry support.

Claim boundaries:

- token estimates based on characters/4 are estimates, not billing;
- the Live Console itself does not save model tokens;
- a deterministic policy is not automatically an optimal policy;
- cache reuse is useful only while the carried context remains relevant;
- universal cost or quality improvements require matched prospective evaluation.

See [Runtime Evaluation](docs/runtime-evaluation.md) and the
[Token-Efficient Runtime design](docs/token-efficient-runtime.md).

---

## Documentation

- [Getting Started](docs/getting-started.md)
- [Architecture](docs/architecture.md)
- [Context Planning](docs/context-planning.md)
- [Cache-Aware Rotation](docs/cache-aware-rotation.md)
- [Token-Efficient Runtime](docs/token-efficient-runtime.md)
- [Live Terminal UI](docs/live-terminal-ui.md)
- [Runtime Supervisor](docs/runtime-supervisor.md)
- [Codex Adapter](docs/codex-adapter.md)
- [Migration 0.4 → 0.5](docs/migration-v4-to-v5.md)
- [Research Methodology](docs/research-methodology.md)
- [Company Adoption](docs/company-adoption.md)

---

## Current limitations

- automatic execution currently targets the local Codex CLI;
- provider usage fields depend on the installed Codex version;
- context token counts are approximate until provider tokenization is available;
- cache-aware defaults are operating policies, not universal optima;
- strict budgets require project-specific calibration;
- a fresh read-only Codex session can inspect repository state, but concurrent writers
  must not modify the same workstream.

---

## Contributing

```bash
git clone https://github.com/hanklin9188/repository-state-agent-workflow.git
cd repository-state-agent-workflow
python -m pip install -e '.[dev]'
ruff check .
pytest -q
rsaw verify .
rsaw context . --strict
rsaw run . --dry-run
```

RSAW is MIT licensed. Markdown and Git remain the durable authority; the runtime,
context planner, and console are replaceable execution layers.
''',
)

write(
    "README.zh-TW.md",
    '''<p align="center">
  <img src="docs/assets/banner.svg" alt="Repository-State Agent Workflow" width="100%" />
</p>

<h1 align="center">Repository-State Agent Workflow</h1>

<p align="center">
  <strong>持久工作流、快取感知的 context、可即時觀測的執行。</strong>
</p>

<p align="center">
  RSAW 將長期專案記憶保存在 repository，明確規劃最小 context，僅在快取與
  任務關聯仍有價值時沿用 Codex thread，於真正邊界自動 ROTATE，並在 VS Code
  Integrated Terminal 中提供清楚的即時 Runtime Console。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.5.0-7c3aed" alt="Version 0.5.0" />
  <img src="https://img.shields.io/badge/python-3.10%2B-2563eb" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/context-cache_aware-0891b2" alt="Cache-aware context" />
  <img src="https://img.shields.io/badge/UI-live_terminal-0f766e" alt="Live terminal UI" />
</p>

---

## RSAW 是什麼

RSAW 是供長時間 coding / research agent 使用的 **repository-first operating
model 與 runtime supervisor**。

- repository 保存 durable memory；
- context epoch 是有上限、可替換的 worker；
- 每個 checkpoint 經驗證後，只會得到四種 action：
  `CONTINUE / ROTATE / PAUSE / COMPLETE`。

0.5 版在 0.4 Live Runtime Console 上增加兩個核心能力：

1. **Cache-aware Context Planner**：穩定 prefix 與動態 authority 分離；
2. **Deterministic Rotation Policy**：同時考慮 turn、hard/soft input、fresh input
   與 cache reuse，不交由模型自行決定 context 壽命。

<p align="center">
  <img src="docs/assets/runtime-architecture-v05.svg" alt="RSAW 0.5 架構" width="100%" />
</p>

> **Workstream 持續存在；context 被規劃、量測並可安全替換。**

---

## 快速開始

```bash
python -m pip install \
  git+https://github.com/hanklin9188/repository-state-agent-workflow.git

cd /path/to/project
rsaw init .
rsaw verify .
rsaw context .
rsaw doctor . --agent codex
rsaw preview . --seconds 6
rsaw run . --agent codex
```

嚴格檢查 bootstrap budget：

```bash
rsaw context . --strict
```

需要原始 log：

```bash
rsaw run . --agent codex --no-tui
```

---

## Context Planner

`rsaw context .` 會產生可重現的 context manifest：

```text
Stable prefix
  AGENTS.md

Dynamic authority
  ACTIVE.md
  active task
  bounded required reads
```

每個檔案都有 path、category、bytes、約略 tokens 與 SHA-256。CONTINUE 只需重新
讀動態 authority；stable fingerprint 未變時，不應重讀 stable prefix。ROTATE
才重新建立完整但最小的 bootstrap。

<p align="center">
  <img src="docs/assets/context-lifecycle.svg" alt="Context lifecycle" width="100%" />
</p>

預設設定：

```json
{
  "runtime": {
    "context": {
      "bootstrap_token_budget": 15000,
      "max_files": 12,
      "max_file_bytes": 262144,
      "include_workstream_spec": false,
      "enforce_budget": false
    }
  }
}
```

---

## Rotation Policy

RSAW 會先遵守角色、審查與科學邊界，再依照 deterministic policy 評估：

```text
MAX_TURNS_PER_RUNTIME_EPOCH
HARD_INPUT_TOKEN_PRESSURE
FRESH_INPUT_TOKEN_PRESSURE
LOW_CACHE_REUSE_AT_SOFT_LIMIT
```

```json
{
  "runtime": {
    "rotation": {
      "soft_input_tokens": 48000,
      "hard_input_tokens": 60000,
      "max_fresh_input_tokens": 18000,
      "min_cache_reuse_ratio": 0.5
    }
  }
}
```

目標不是讓 cached token 越多越好，而是：

```text
有用的 cache reuse
+ 更少 stale context
+ ROTATE 後的小型 fresh bootstrap
+ 每個成功 checkpoint 更低的 fresh-input cost
```

---

## Live Runtime Console

<p align="center">
  <img src="docs/assets/live-terminal-dashboard.svg" alt="RSAW Live Runtime Console" width="100%" />
</p>

在 VS Code Terminal 直接顯示：

- **NOW**：Codex 現在讀檔、改檔、執行 command 或驗證；
- **PROGRESS**：workstream、task、role、epoch、checkpoint、下一個 action；
- **CONTEXT**：soft/hard pressure、cached、fresh input；
- **RECENT**：重要事件，不洗版 raw JSON；
- **GATE**：是否需要人工介入。

TUI 是本機 presentation layer，不會把 dashboard 文字放進 prompt，也不會新增
model turn。真正的 context/token 效率來自 repository state、bounded epoch、
CONTINUE、ROTATE 與 progressive disclosure。

---

## 指標

```text
fresh input = max(0, input - cached input)
cache reuse ratio = cached input / input
input per checkpoint = total input / accepted checkpoints
fresh input per checkpoint = fresh input / accepted checkpoints
```

```bash
rsaw report .
rsaw report . --json
```

---

## 安全邊界

- 每個 supervised turn 前後都驗證 repository；
- 成功 turn 必須推進 `ACTIVE.md`；
- single-supervisor lock 防止兩個 writer；
- human gate 不推測授權；
- 失敗的正式執行不自動重試；
- role / scientific boundary 必須 fresh；
- context planner 與 TUI 都不能改變 lifecycle authority。

---

## 證據與限制

目前有 cross-version CI、context-plan / rotation-policy unit tests、runtime/TUI
測試與歷史 case study。以下仍不可過度宣稱：

- chars/4 是估算，不是 provider billing；
- TUI 本身不省 token；
- deterministic default 不等於所有專案的最佳參數；
- universal token / quality improvement 仍需 matched prospective study。

---

## 文件

- [Architecture](docs/architecture.md)
- [Context Planning](docs/context-planning.md)
- [Cache-Aware Rotation](docs/cache-aware-rotation.md)
- [Token-Efficient Runtime](docs/token-efficient-runtime.md)
- [Live Terminal UI](docs/live-terminal-ui.md)
- [Migration 0.4 → 0.5](docs/migration-v4-to-v5.md)
- [Runtime Evaluation](docs/runtime-evaluation.md)

RSAW 採 MIT License。Markdown 與 Git 仍是 durable authority；runtime、planner
與 console 都是可替換的執行層。
''',
)

write(
    "docs/architecture.md",
    '''# Architecture

## Design invariant

```text
Repository authority > runtime state > model context > presentation
```

RSAW 0.5 separates six layers:

1. **Repository authority** — `AGENTS.md`, accepted decisions, `ACTIVE.md`, active task.
2. **Context planner** — ordered, fingerprinted, budgeted read manifest.
3. **Continuation engine** — CONTINUE / ROTATE / PAUSE / COMPLETE.
4. **Runtime supervisor** — bounded Codex turns, verification, locks, limits.
5. **Telemetry** — provider usage, checkpoints, transitions, evidence paths.
6. **Live console** — non-authoritative operator presentation.

![RSAW 0.5 architecture](assets/runtime-architecture-v05.svg)

## Data flow

```text
AGENTS + ACTIVE + task
        ↓
ContextPlan
        ↓
Fresh prompt or continuation delta
        ↓
Codex exec / resume
        ↓
Structured events + repository mutation
        ↓
Verification + checkpoint
        ↓
Deterministic rotation evaluation
        ↓
CONTINUE / ROTATE / PAUSE / COMPLETE
```

## Context-plan authority

The planner does not decide project truth. It serializes the files already authorized
by repository state, removes duplicates, verifies repository locality, records hashes,
and checks an operating budget.

## Rotation authority

Mandatory role/scientific boundaries come from repository state. Runtime pressure is
deterministic and uses configured thresholds plus provider-emitted usage. The model
never chooses whether its own context should survive.

## Presentation isolation

Codex and supervisor event sinks are best-effort. Exceptions in the Live Console are
caught and cannot alter the worker, checkpoint verification, or lifecycle result.

## Compatibility

The 0.4 flat `rotate_input_tokens` field remains accepted. New repositories receive
schema version 2 with explicit `context` and `rotation` sections.
''',
)

write(
    "docs/context-planning.md",
    '''# Context Planning

## Goal

Make every fresh or continued model turn start from an explicit, inspectable context
contract instead of an implicit repository scan.

## Ordered plan

```text
Stable prefix
  1. AGENTS.md
  2. optional stable workstream specification

Dynamic authority
  1. ACTIVE.md
  2. active task
  3. deduplicated Required Reads
```

`rsaw context .` records path, category, bytes, approximate tokens, and SHA-256 for
each document. Files must remain inside the repository and within configured size and
count limits.

## Stable and dynamic fingerprints

The stable fingerprint changes only when stable policy changes. The dynamic fingerprint
changes with task/handoff state. A continued context receives a small instruction to
reread dynamic authority and reuse the stable prefix when its fingerprint is unchanged.

## Budget behavior

By default, an over-budget plan produces a warning so existing repositories remain
compatible. Projects can enable `runtime.context.enforce_budget` or run:

```bash
rsaw context . --strict
```

Strict mode is appropriate only after the project has calibrated its task and evidence
sizes.

## Security

The planner rejects paths outside the repository, missing files, non-UTF-8 authority,
files above the configured byte limit, and excessive file counts.

## Claim boundary

Approximate tokens use UTF-8 text characters divided by four. This is a planning
estimate, not provider tokenization or billing.
''',
)

write(
    "docs/cache-aware-rotation.md",
    '''# Cache-Aware Rotation

## Objective

Preserve useful task-local cache reuse without carrying obsolete context indefinitely.

## Decision order

Repository-declared boundaries remain authoritative. When continuation is otherwise
allowed, RSAW evaluates runtime pressure in this order:

1. maximum turns per epoch;
2. hard latest-turn input threshold;
3. maximum fresh/uncached input;
4. soft threshold combined with low cache reuse;
5. continue when cache locality remains acceptable.

## Metrics

```text
fresh_input = max(0, input_tokens - cached_input_tokens)
cache_reuse_ratio = cached_input_tokens / input_tokens
```

Missing usage does not trigger a cache-quality rotation. Hard role, review, safety, and
scientific boundaries still rotate independently of token telemetry.

## Why both soft and hard thresholds

A hard threshold bounds context size. A soft threshold permits continuation when the
prefix is still highly reusable, but rotates earlier when a large input carries little
useful cache reuse.

## Configuration

```json
{
  "runtime": {
    "rotation": {
      "soft_input_tokens": 48000,
      "hard_input_tokens": 60000,
      "max_fresh_input_tokens": 18000,
      "min_cache_reuse_ratio": 0.5
    }
  }
}
```

These are conservative operating defaults, not universal optima. Calibrate them with
matched tasks and report fresh input per successful checkpoint.
''',
)

write(
    "docs/token-efficient-runtime.md",
    '''# Token-Efficient Runtime Design

## Product goal

Provide more operator visibility while reducing unnecessary model context traffic.

## Mechanisms

- repository-backed durable state;
- explicit context manifests;
- stable-prefix and dynamic-authority separation;
- continuation prompts that avoid rereading unchanged policy;
- deterministic cache-aware rotation;
- checkpoint-normalized token reporting;
- local TUI rendering with zero intentional model-token overhead.

## Primary KPI

```text
fresh input tokens / successful checkpoint
```

Supporting metrics:

- successful checkpoint rate;
- total input;
- cached input;
- fresh input;
- output;
- turns and epochs;
- rotations;
- manual relays;
- wall time per successful checkpoint.

## Non-goals

- maximizing cache hit rate regardless of relevance;
- replacing provider token accounting;
- weakening role/scientific boundaries;
- inferring human authorization;
- claiming a causal improvement before a matched prospective study.

## Evaluation

Compare the same task, model, repository revision, permissions, validation oracle, and
starting state. Separate implementation correctness from causal efficiency claims.
''',
)

write(
    "docs/live-terminal-ui.md",
    '''# Live Terminal UI

## Purpose

The Live Runtime Console turns structured Codex and supervisor events into an
operator-facing view inside normal terminals, especially VS Code Integrated Terminal.

## Information hierarchy

1. **NOW** — observable current activity.
2. **PROGRESS** — task, role, epoch, checkpoint, next action.
3. **CONTEXT** — pressure, cached input, fresh input, rotation reason.
4. **RECENT** — three to five high-value events.
5. **FOOTER** — durable state, gate, elapsed runtime.

## Motion

Motion communicates state only: one heartbeat, one activity spinner, smooth pressure
interpolation, checkpoint acceptance, and a brief ROTATE transition. PAUSE, FAILED,
and COMPLETE use stable unambiguous terminal states.

## Responsive behavior

Expanded layout is used when width and height permit. Compact layout keeps NOW,
checkpoint, action, context pressure, fresh input, and the latest event. Non-TTY output
uses plain logs without ANSI control sequences.

## Privacy and authority

The UI never displays hidden chain-of-thought. Reasoning events become a neutral
observable label. The model and renderer cannot decide continuation or change
repository authority.
''',
)

write(
    "docs/runtime-supervisor.md",
    '''# Runtime Supervisor

RSAW supervises a persistent repository workstream while Codex contexts remain bounded.

## Start

```bash
rsaw verify .
rsaw context .
rsaw doctor . --agent codex
rsaw run . --agent codex
```

## Per-turn contract

Each supervised turn must complete exactly one durable checkpoint. RSAW then verifies:

1. adapter success;
2. `ACTIVE.md` advancement;
3. repository validity;
4. context-plan validity/warnings;
5. the next continuation action;
6. runtime rotation pressure.

## Context lifecycle

- Fresh epoch: full ordered minimal bootstrap.
- Continued epoch: reread dynamic authority; reuse unchanged stable policy.
- Rotation: clear the thread and begin another fresh epoch.

## Failure semantics

RSAW fails closed. It does not retry failed agent or formal turns automatically, invent
approval, or let presentation errors affect execution.

## Runtime evidence

`.rsaw/runtime/<run-id>/` contains summary JSON, supervisor JSONL, Codex events, and the
last message. `rsaw report .` derives checkpoint-normalized context metrics.
''',
)

write(
    "docs/codex-adapter.md",
    '''# Codex Runtime Adapter

The automatic adapter uses local Codex CLI structured execution:

```text
fresh     codex exec --json ... -
continue  codex exec --json ... resume <thread-id> -
```

Prompts are passed through stdin. The adapter records thread IDs, terminal events, and
provider-emitted usage. It never enables the dangerous sandbox bypass.

## Context integration

RSAW sets an ordered prompt contract and passes the stable-prefix fingerprint in the
worker environment. Continued prompts avoid asking Codex to reread unchanged stable
policy; fresh prompts provide the complete minimal read order.

## Observability

Structured events feed both durable JSONL and the best-effort Live Console. Event-sink
exceptions are isolated from the worker.

## Requirements

- `codex` on `PATH` or `--codex-bin`;
- authenticated CLI;
- support for `exec`, `--json`, resume, and last-message output;
- a verified RSAW repository.

Check with:

```bash
rsaw doctor . --agent codex
```
''',
)

write(
    "docs/migration-v4-to-v5.md",
    '''# Migration 0.4 → 0.5

## Compatibility

RSAW 0.5 accepts the 0.4 flat `rotate_input_tokens` configuration. Existing repositories
do not require `rsaw init --force`.

## Recommended update

1. Upgrade the package.
2. Run `rsaw verify .`.
3. Run `rsaw context .` and inspect the plan.
4. Add nested `rotation` and `context` settings when ready.
5. Preview the console.
6. Run a non-destructive pilot before changing production thresholds.

```bash
python -m pip install --upgrade \
  git+https://github.com/hanklin9188/repository-state-agent-workflow.git

rsaw verify .
rsaw context .
rsaw preview .
rsaw run . --dry-run
```

## Do not

- use `rsaw init --force` on a customized repository;
- enable strict context budgets before measuring existing task sizes;
- assume the default rotation thresholds are optimal;
- hot-upgrade a supervisor process that already owns the repository.
''',
)

write(
    "CHANGELOG.md",
    '''# Changelog

All notable changes to the public reference implementation are documented here.

## 0.5.0 — Cache-Aware Context Runtime

### Added

- deterministic ordered context manifests with stable/dynamic fingerprints;
- `rsaw context` inspection and optional strict budget gate;
- repository-local path, file-count, byte, and approximate-token validation;
- continuation prompts that avoid rereading unchanged stable policy;
- nested `runtime.context` and `runtime.rotation` configuration;
- deterministic rotation on hard pressure, fresh-input pressure, and low cache reuse;
- fresh-input, cache-reuse, and checkpoint-normalized runtime reports;
- context-planning, rotation-policy, CLI, compatibility, and prompt tests;
- revised terminal visuals, architecture diagrams, README, and migration docs.

### Preserved

- CONTINUE / ROTATE / PAUSE / COMPLETE semantics;
- mandatory role, review, and scientific boundaries;
- repository state as durable authority;
- Codex `exec --json`, sandbox policy, locks, and fail-closed verification;
- Live Console as a non-authoritative local presentation layer;
- backward compatibility for the 0.4 flat rotation threshold.

### Claim boundary

Context budgets use approximate token counts. Cache-aware defaults are operating
policies, not universal optima. Causal token or quality improvement still requires a
matched prospective evaluation.

## 0.4.0 — Live Runtime Console

- in-place interactive terminal dashboard;
- compact/expanded responsive layouts;
- NOW, progress, context pressure, recent events, gates, and terminal states;
- `rsaw preview`, `--tui`, `--no-tui`, and non-TTY fallback;
- isolated Codex/supervisor event hooks and presentation tests.

## 0.3.0 — Automatic Workstream Runtime

- automatic Codex CONTINUE and ROTATE;
- explicit PAUSE and COMPLETE;
- token telemetry, runtime reports, locks, limits, and fail-closed state advancement.

## 0.2.0 — Persistent Workstreams and Context Epochs

- durable workstreams, bounded context epochs, task checkpoints, and role-specific prompts.

## 0.1.0 — Initial Public Release

- repository-state methodology, templates, CLI verification, and bootstrap case study.
''',
)

write(
    "ROADMAP.md",
    '''# Roadmap

## 0.5 — Cache-Aware Context Runtime

- [x] deterministic context plan and fingerprints
- [x] fresh vs continued read contracts
- [x] context budgets and `rsaw context`
- [x] cache-aware deterministic rotation
- [x] checkpoint-normalized context metrics
- [x] updated Live Console visuals and documentation
- [ ] controlled prospective matched study
- [ ] calibrate defaults from measured workloads

## 0.6 candidates

- provider-tokenizer-backed plan estimates when available;
- pluggable context-policy profiles;
- read-only observer/attach mode for an active workstream;
- richer long-running external-job telemetry;
- additional agent adapters without weakening repository authority.

## Explicitly deferred

- web dashboard;
- project-management platform behavior;
- hidden-memory database;
- unsafe autonomous approvals;
- universal token-savings claims without matched evidence.
''',
)

write(
    "CITATION.cff",
    '''cff-version: 1.2.0
message: "If this workflow or evaluation framework helps your work, cite the repository and exact version used."
title: "Repository-State Agent Workflow"
type: software
authors:
  - name: Hank
repository-code: "https://github.com/hanklin9188/repository-state-agent-workflow"
url: "https://github.com/hanklin9188/repository-state-agent-workflow"
license: MIT
version: 0.5.0
date-released: 2026-08-15
keywords:
  - coding agents
  - repository state
  - context planning
  - cache efficiency
  - persistent workstreams
  - context epochs
  - context rotation
  - runtime supervisor
  - terminal user interface
  - agent observability
  - context engineering
''',
)

write(
    "REPOSITORY_METADATA.json",
    json.dumps(
        {
            "name": "repository-state-agent-workflow",
            "owner": "hanklin9188",
            "visibility": "public",
            "description": (
                "Repository-backed agent workstreams with cache-aware context planning, "
                "automatic Codex rotation, and a live terminal runtime console."
            ),
            "license": "MIT",
            "topics": [
                "coding-agents",
                "ai-agents",
                "agent-workflow",
                "repository-state",
                "context-engineering",
                "context-planning",
                "cache-efficiency",
                "persistent-workstreams",
                "context-rotation",
                "codex",
                "terminal-ui",
                "developer-tools",
            ],
            "social_preview": "docs/assets/social-preview.png",
            "live_console_preview": "docs/assets/live-terminal-dashboard.svg",
            "architecture_preview": "docs/assets/runtime-architecture-v05.svg",
        },
        indent=2,
    ),
)

write(
    "ACTIVE.md",
    '''# Active Handoff

## Repository

Branch: resolve with `git branch --show-current`
HEAD: resolve with `git rev-parse HEAD`
Status: RSAW 0.5 cache-aware runtime release candidate

## Workstream

ID: W-005
Spec: docs/workstreams/W-005-token-efficient-runtime.md

## Context Epoch

ID: E-008-token-runtime-review
Role: Reviewer

## Active Task

ID: T-008
Spec: docs/tasks/T-008-token-efficient-runtime-validation.md

## Current State

- Ordered context manifests and stable/dynamic fingerprints are implemented.
- Fresh and continued prompts use different read contracts.
- Deterministic rotation includes hard, fresh-input, and low-cache-reuse pressure.
- Runtime reports expose fresh input and checkpoint-normalized efficiency.
- Live Console visuals and public documentation reflect the 0.5 architecture.
- Causal token and quality claims remain unpromoted pending matched evaluation.

## Evidence

- Context planner: `src/repo_state_agent/runtime/context.py`
- Rotation policy: `src/repo_state_agent/runtime/rotation.py`
- Supervisor integration: `src/repo_state_agent/runtime/supervisor.py`
- CLI/report integration: `src/repo_state_agent/cli.py`, `src/repo_state_agent/runtime/report.py`
- Tests: `tests/test_context_plan.py`, `tests/test_rotation_policy.py`
- Design: `docs/token-efficient-runtime.md`

## Required Reads

- AGENTS.md
- ACTIVE.md
- docs/tasks/T-008-token-efficient-runtime-validation.md

## Context Contract

Mode: BOUNDED
Stable Prefix: AGENTS.md
Budget: `.rsaw/config.json`

## Do Not Preload

- archived release reports;
- raw CI logs unless a check fails;
- all case-study data;
- full Codex event streams.

## Human Gate

None.

## Running or Pending External Work

GitHub CI and operator preview after the implementation commit.

## Blockers

None.

## Next Exact Action

Run cross-version CI, inspect failures, preview the console in a real VS Code Terminal,
and review context/rotation defaults without making causal efficiency claims.

## Stop Condition

Ruff, pytest, repository verification, strict context plan, dry-run, report, and link
checks pass; the release candidate is ready for an operator pilot.

## Continuation Gate

Decision: ROTATE_REQUIRED
Reason: IMPLEMENTATION_TO_INDEPENDENT_VALIDATION_BOUNDARY

## Next Task

ID: T-009
Spec: docs/tasks/T-009-token-efficient-runtime-prospective-study.md

## Next Session Role

Runner

## Recommended Reasoning

Medium

## Last Updated

2026-08-15 — RSAW 0.5 cache-aware runtime release candidate
''',
)

write(
    "docs/workstreams/W-005-token-efficient-runtime.md",
    '''# W-005 — Token-Efficient Runtime

## Goal

Turn repository-backed continuity into an explicit, measurable context policy while
preserving lifecycle, safety, and scientific boundaries.

## State Machine

```text
Design
→ context planner
→ cache-aware rotation
→ reporting and TUI integration
→ cross-version validation
→ operator pilot
→ matched prospective study
```

## Required Properties

- repository authority remains canonical;
- stable and dynamic context are distinguishable and fingerprinted;
- continuation avoids unnecessary stable rereads;
- rotation is deterministic and bounded;
- human/scientific boundaries override token convenience;
- UI and telemetry remain non-authoritative;
- claims do not exceed measured evidence.

## Stop

Implementation is green, operator presentation is reviewed, and a prospective protocol
is ready without promoting causal claims.
''',
)

write(
    "docs/tasks/T-008-token-efficient-runtime-validation.md",
    '''# T-008 — Token-Efficient Runtime Validation

## Goal

Independently validate the RSAW 0.5 implementation and public presentation.

## Acceptance Criteria

- legacy and nested config parse correctly;
- context plans are ordered, deduplicated, local, fingerprinted, and budgeted;
- fresh and continuation prompts preserve the intended read contract;
- rotation reason precedence is deterministic;
- existing supervisor, Codex, and TUI tests remain green;
- `rsaw context . --strict` passes for this repository;
- README diagrams and local Markdown links are valid;
- no causal token-saving claim is promoted.

## Validation

```bash
ruff check .
pytest -q
rsaw verify .
rsaw context . --strict
rsaw run . --dry-run
rsaw report . --json
python scripts/check_markdown_links.py .
```

## Stop Condition

All implementation and documentation checks pass and findings are recorded.
''',
)

write(
    "docs/tasks/T-009-token-efficient-runtime-prospective-study.md",
    '''# T-009 — Token-Efficient Runtime Prospective Study

## Goal

Evaluate RSAW 0.5 against matched control conditions without changing the implementation
or oracle after observing outcomes.

## Metrics

- attempted and successful checkpoints;
- success rate;
- total, cached, fresh, and output tokens;
- input and fresh input per successful checkpoint;
- context epochs and rotations;
- manual relays and true human gates;
- wall time per successful checkpoint.

## Boundaries

Use identical repository revisions, tasks, models, permissions, validation, and starting
state. Seal raw evidence before interpretation. Do not tune thresholds on the formal test.

## Stop Condition

A preregistered pilot protocol and independent validator are ready.
''',
)

write(
    "docs/releases/rsaw-v5-token-efficient-runtime.md",
    '''# RSAW 0.5 — Cache-Aware Context Runtime

RSAW 0.5 adds an explicit context planning layer, stable/dynamic fingerprints,
continuation read discipline, deterministic cache-aware rotation, and
checkpoint-normalized context metrics. The 0.4 Live Runtime Console remains the default
interactive experience and has been updated to communicate the new operating model.

The release does not claim universal token savings. It provides the implementation and
telemetry required for a matched prospective study.
''',
)

write(
    ".github/workflows/ci.yml",
    '''name: CI

on:
  push:
  pull_request:

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.10", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
      - run: python -m pip install --upgrade pip
      - run: python -m pip install -e '.[dev]'
      - run: ruff check .
      - run: pytest -q
      - run: rsaw verify .
      - run: rsaw context . --strict
      - run: rsaw footprint . --max-tokens 15000
      - run: rsaw run . --dry-run
      - run: rsaw report . --json
      - run: python scripts/check_markdown_links.py .
''',
)

write(
    "docs/assets/banner.svg",
    '''<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="340" viewBox="0 0 1400 340">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#07111f"/>
      <stop offset="0.55" stop-color="#0b2130"/>
      <stop offset="1" stop-color="#0f3d3e"/>
    </linearGradient>
    <linearGradient id="line" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#22d3ee"/>
      <stop offset="1" stop-color="#34d399"/>
    </linearGradient>
  </defs>
  <rect width="1400" height="340" rx="28" fill="url(#bg)"/>
  <g opacity="0.18" stroke="#67e8f9">
    <path d="M0 82H1400M0 170H1400M0 258H1400"/>
    <path d="M140 0V340M350 0V340M560 0V340M770 0V340M980 0V340M1190 0V340"/>
  </g>
  <rect x="80" y="72" width="150" height="150" rx="34" fill="#0d2c3a" stroke="url(#line)" stroke-width="4"/>
  <path d="M119 132h72M119 165h72M119 198h50" stroke="#67e8f9" stroke-width="12" stroke-linecap="round"/>
  <circle cx="191" cy="198" r="12" fill="#34d399"/>
  <text x="270" y="135" fill="#f8fafc" font-family="Inter,Segoe UI,sans-serif" font-size="58" font-weight="700">Repository-State Agent Workflow</text>
  <text x="272" y="190" fill="#a5f3fc" font-family="Inter,Segoe UI,sans-serif" font-size="28">Persistent workstreams · Cache-aware contexts · Live operator visibility</text>
  <path d="M272 232H1120" stroke="url(#line)" stroke-width="6" stroke-linecap="round"/>
  <g font-family="Inter,Segoe UI,sans-serif" font-size="22" font-weight="600">
    <text x="272" y="278" fill="#5eead4">CONTEXT PLAN</text>
    <text x="520" y="278" fill="#67e8f9">CONTINUE</text>
    <text x="700" y="278" fill="#fbbf24">ROTATE</text>
    <text x="858" y="278" fill="#fde68a">PAUSE</text>
    <text x="1000" y="278" fill="#86efac">COMPLETE</text>
  </g>
</svg>
''',
)

write(
    "docs/assets/runtime-architecture-v05.svg",
    '''<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="650" viewBox="0 0 1400 650">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#07111f"/><stop offset="1" stop-color="#102a35"/></linearGradient>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#67e8f9"/></marker>
  </defs>
  <rect width="1400" height="650" rx="28" fill="url(#bg)"/>
  <text x="70" y="70" fill="#f8fafc" font-family="Inter,Segoe UI,sans-serif" font-size="36" font-weight="700">RSAW 0.5 · Cache-Aware Runtime Architecture</text>
  <text x="70" y="108" fill="#94a3b8" font-family="Inter,Segoe UI,sans-serif" font-size="20">Repository authority remains canonical; planning, execution and presentation stay separated.</text>
  <g font-family="Inter,Segoe UI,sans-serif">
    <g><rect x="70" y="170" width="245" height="150" rx="22" fill="#102c3a" stroke="#34d399" stroke-width="3"/><text x="100" y="210" fill="#6ee7b7" font-size="20" font-weight="700">REPOSITORY AUTHORITY</text><text x="100" y="250" fill="#e2e8f0" font-size="18">AGENTS.md</text><text x="100" y="278" fill="#e2e8f0" font-size="18">ACTIVE.md</text><text x="100" y="306" fill="#e2e8f0" font-size="18">Active task + evidence</text></g>
    <g><rect x="375" y="170" width="245" height="150" rx="22" fill="#102c3a" stroke="#22d3ee" stroke-width="3"/><text x="405" y="210" fill="#67e8f9" font-size="20" font-weight="700">CONTEXT PLANNER</text><text x="405" y="250" fill="#e2e8f0" font-size="18">Stable prefix hash</text><text x="405" y="278" fill="#e2e8f0" font-size="18">Dynamic authority</text><text x="405" y="306" fill="#e2e8f0" font-size="18">Budget + manifest</text></g>
    <g><rect x="680" y="170" width="245" height="150" rx="22" fill="#102c3a" stroke="#a78bfa" stroke-width="3"/><text x="710" y="210" fill="#c4b5fd" font-size="20" font-weight="700">SUPERVISOR</text><text x="710" y="250" fill="#e2e8f0" font-size="18">Bounded Codex turn</text><text x="710" y="278" fill="#e2e8f0" font-size="18">Verify checkpoint</text><text x="710" y="306" fill="#e2e8f0" font-size="18">Locks + safety gates</text></g>
    <g><rect x="985" y="170" width="345" height="150" rx="22" fill="#102c3a" stroke="#fbbf24" stroke-width="3"/><text x="1015" y="210" fill="#fde68a" font-size="20" font-weight="700">ROTATION POLICY</text><text x="1015" y="250" fill="#e2e8f0" font-size="18">Turns · hard input</text><text x="1015" y="278" fill="#e2e8f0" font-size="18">Fresh input · cache reuse</text><text x="1015" y="306" fill="#e2e8f0" font-size="18">CONTINUE or fresh ROTATE</text></g>
    <path d="M315 245H365" stroke="#67e8f9" stroke-width="4" marker-end="url(#arrow)"/><path d="M620 245H670" stroke="#67e8f9" stroke-width="4" marker-end="url(#arrow)"/><path d="M925 245H975" stroke="#67e8f9" stroke-width="4" marker-end="url(#arrow)"/>
    <g><rect x="250" y="410" width="900" height="145" rx="24" fill="#0c2230" stroke="#38bdf8" stroke-width="2"/><text x="290" y="452" fill="#7dd3fc" font-size="21" font-weight="700">LIVE RUNTIME CONSOLE · non-authoritative observer</text><text x="290" y="490" fill="#e2e8f0" font-size="18">NOW · task progress · context pressure · cached/fresh input · rotation reason · human gate</text><text x="290" y="526" fill="#94a3b8" font-size="17">Structured events flow down; presentation errors never flow back into lifecycle decisions.</text></g>
    <path d="M800 320V400" stroke="#38bdf8" stroke-width="4" marker-end="url(#arrow)"/><path d="M1155 320V380H1060V400" stroke="#38bdf8" stroke-width="4" marker-end="url(#arrow)"/>
  </g>
</svg>
''',
)

write(
    "docs/assets/context-lifecycle.svg",
    '''<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="520" viewBox="0 0 1400 520">
  <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#07111f"/><stop offset="1" stop-color="#12303a"/></linearGradient><marker id="a" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#67e8f9"/></marker></defs>
  <rect width="1400" height="520" rx="28" fill="url(#bg)"/>
  <text x="70" y="66" fill="#f8fafc" font-family="Inter,Segoe UI,sans-serif" font-size="34" font-weight="700">Context Lifecycle</text>
  <g font-family="Inter,Segoe UI,sans-serif">
    <rect x="70" y="125" width="300" height="235" rx="22" fill="#102c3a" stroke="#34d399" stroke-width="3"/><text x="100" y="170" fill="#6ee7b7" font-size="22" font-weight="700">STABLE PREFIX</text><text x="100" y="212" fill="#e2e8f0" font-size="19">AGENTS.md</text><text x="100" y="244" fill="#e2e8f0" font-size="19">Optional stable authority</text><text x="100" y="298" fill="#94a3b8" font-size="17">Fingerprint changes rarely</text><text x="100" y="328" fill="#94a3b8" font-size="17">Reuse inside an epoch</text>
    <rect x="425" y="125" width="300" height="235" rx="22" fill="#102c3a" stroke="#22d3ee" stroke-width="3"/><text x="455" y="170" fill="#67e8f9" font-size="22" font-weight="700">DYNAMIC AUTHORITY</text><text x="455" y="212" fill="#e2e8f0" font-size="19">ACTIVE.md</text><text x="455" y="244" fill="#e2e8f0" font-size="19">Active task</text><text x="455" y="276" fill="#e2e8f0" font-size="19">Bounded required reads</text><text x="455" y="328" fill="#94a3b8" font-size="17">Re-read on CONTINUE</text>
    <rect x="780" y="125" width="250" height="235" rx="22" fill="#102c3a" stroke="#a78bfa" stroke-width="3"/><text x="810" y="170" fill="#c4b5fd" font-size="22" font-weight="700">CONTINUE</text><text x="810" y="215" fill="#e2e8f0" font-size="18">Same thread</text><text x="810" y="247" fill="#e2e8f0" font-size="18">Keep useful cache</text><text x="810" y="300" fill="#94a3b8" font-size="17">Stable unchanged</text><text x="810" y="330" fill="#94a3b8" font-size="17">Dynamic refreshed</text>
    <rect x="1085" y="125" width="245" height="235" rx="22" fill="#102c3a" stroke="#fbbf24" stroke-width="3"/><text x="1115" y="170" fill="#fde68a" font-size="22" font-weight="700">ROTATE</text><text x="1115" y="215" fill="#e2e8f0" font-size="18">Fresh thread</text><text x="1115" y="247" fill="#e2e8f0" font-size="18">Drop stale history</text><text x="1115" y="300" fill="#94a3b8" font-size="17">Minimal full bootstrap</text><text x="1115" y="330" fill="#94a3b8" font-size="17">Rebuild locality</text>
    <path d="M370 242H415" stroke="#67e8f9" stroke-width="4" marker-end="url(#a)"/><path d="M725 242H770" stroke="#67e8f9" stroke-width="4" marker-end="url(#a)"/><path d="M1030 242H1075" stroke="#67e8f9" stroke-width="4" marker-end="url(#a)"/>
    <text x="70" y="430" fill="#5eead4" font-size="20" font-weight="700">Optimization target</text><text x="275" y="430" fill="#e2e8f0" font-size="20">useful cache reuse + low stale carryover + small fresh bootstrap + verified progress per token</text>
  </g>
</svg>
''',
)

write(
    "docs/assets/live-terminal-dashboard.svg",
    '''<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="860" viewBox="0 0 1500 860">
  <rect width="1500" height="860" rx="30" fill="#070d16"/>
  <rect x="45" y="45" width="1410" height="770" rx="22" fill="#0b1420" stroke="#22d3ee" stroke-width="3"/>
  <g font-family="ui-monospace,SFMono-Regular,Consolas,monospace">
    <text x="80" y="92" fill="#67e8f9" font-size="25" font-weight="700">RSAW · EdgeFlow</text><text x="1260" y="92" fill="#34d399" font-size="23">● WORKING</text>
    <text x="80" y="130" fill="#94a3b8" font-size="19">Builder · Runtime epoch 3 · Context plan PASS</text>
    <text x="80" y="185" fill="#64748b" font-size="18" font-weight="700">NOW</text><text x="170" y="185" fill="#f8fafc" font-size="22">Running focused validation</text><text x="170" y="218" fill="#94a3b8" font-size="18">pytest tests/runtime/test_gpu_observer.py</text>
    <text x="80" y="278" fill="#64748b" font-size="18" font-weight="700">PROGRESS</text><text x="215" y="278" fill="#67e8f9" font-size="20" font-weight="700">E04 · GPU Observability</text>
    <text x="215" y="320" fill="#34d399" font-size="19">✓ Design   ✓ Implement</text><text x="510" y="320" fill="#67e8f9" font-size="19">● Validate</text><text x="655" y="320" fill="#64748b" font-size="19">○ Run   ○ Analyze</text>
    <text x="215" y="360" fill="#cbd5e1" font-size="18">Checkpoint 6</text><text x="490" y="360" fill="#34d399" font-size="18">Next CONTINUE · same context</text>
    <text x="80" y="425" fill="#64748b" font-size="18" font-weight="700">CONTEXT</text><text x="215" y="425" fill="#34d399" font-size="19" font-weight="700">GOOD</text><text x="330" y="425" fill="#94a3b8" font-size="17">soft 48k · hard 60k · fresh limit 18k</text>
    <rect x="215" y="452" width="900" height="22" rx="11" fill="#172334"/><rect x="215" y="452" width="618" height="22" rx="11" fill="#22d3ee"/><text x="1140" y="470" fill="#e2e8f0" font-size="18">68%</text>
    <text x="215" y="520" fill="#cbd5e1" font-size="18">Input 41.2k</text><text x="455" y="520" fill="#5eead4" font-size="18">Cached 34.8k · 84%</text><text x="765" y="520" fill="#fde68a" font-size="18">Fresh 6.4k</text><text x="990" y="520" fill="#c4b5fd" font-size="18">Fresh/checkpoint 1.1k</text>
    <text x="80" y="585" fill="#64748b" font-size="18" font-weight="700">CONTEXT PLAN</text><text x="245" y="585" fill="#e2e8f0" font-size="18">Stable 1.2k · Dynamic 3.6k · Budget 15k · Prefix a81f…93c0</text>
    <text x="80" y="650" fill="#64748b" font-size="18" font-weight="700">RECENT</text><text x="215" y="650" fill="#34d399" font-size="18">✓ Validation passed · 18/18</text><text x="215" y="686" fill="#e2e8f0" font-size="18">◆ Updated telemetry.py</text><text x="215" y="722" fill="#e2e8f0" font-size="18">↻ Rotation evaluation · cache locality acceptable</text>
    <line x1="80" y1="760" x2="1420" y2="760" stroke="#243447"/><text x="80" y="793" fill="#94a3b8" font-size="17">Durable 3s ago</text><text x="410" y="793" fill="#94a3b8" font-size="17">Gate NONE</text><text x="710" y="793" fill="#94a3b8" font-size="17">Runtime 31m</text><text x="1120" y="793" fill="#67e8f9" font-size="17">RSAW 0.5</text>
  </g>
</svg>
''',
)

print("RSAW 0.5 documentation and visual files staged")
