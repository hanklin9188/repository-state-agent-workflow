<p align="center">
  <img src="docs/assets/banner.svg" alt="Repository-State Agent Workflow banner" width="100%" />
</p>

<h1 align="center">Repository-State Agent Workflow</h1>

<p align="center">
  <strong>Make the repository remember, so the agent does not have to.</strong>
</p>

<p align="center">
  A Markdown-first operating model and small CLI for low-context, high-quality coding-agent work.<br/>
  Move continuity out of hidden conversations and into versioned repository state.
</p>

<p align="center">
  <a href="https://github.com/hanklin9188/repository-state-agent-workflow/actions/workflows/ci.yml"><img src="https://github.com/hanklin9188/repository-state-agent-workflow/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-0f766e" alt="MIT License" /></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%2B-2563eb" alt="Python 3.10+" /></a>
  <img src="https://img.shields.io/badge/status-alpha-f59e0b" alt="Alpha" />
</p>

<p align="center">
  <a href="#five-minute-start">Quick start</a> ·
  <a href="#measured-adoption-evidence">Adoption evidence</a> ·
  <a href="#how-it-works">How it works</a> ·
  <a href="docs/company-adoption.md">Company adoption</a> ·
  <a href="README.zh-TW.md">繁體中文</a>
</p>

---

## Why RSAW

Long-running coding-agent conversations often become accidental state stores. They accumulate stale source snapshots, old logs, failed attempts, completed tasks, obsolete decisions, and repeated project explanations. Every later model call must reason through that mixture again.

RSAW replaces hidden conversational continuity with a small, auditable repository contract:

| Problem | RSAW response |
|---|---|
| Growing conversation history | Fresh, bounded sessions |
| Hidden current state | Versioned `ACTIVE.md` handoff |
| Broad mandatory preload | Three-file bootstrap plus progressive disclosure |
| Repeated investigation | Durable evidence and explicit next action |
| Validation weakened to save context | Staged V0–V3 evidence gates |
| Builder history contaminates review | Fresh, role-separated reviewer sessions |

> **Repository state is authoritative. Conversation history is disposable.**

---

## Measured adoption evidence

### Desk Code Agent — preliminary V1 result

Desk Code Agent replaced a broad mandatory project bootstrap with the RSAW three-file contract: `AGENTS.md`, `ACTIVE.md`, and one active task specification.

| Metric | Previous workflow | RSAW V1 | Change |
|---|---:|---:|---:|
| Fresh-session bootstrap estimate | 33,348 | **2,967** | **-30,381** |
| Relative reduction | — | — | **91.10%** |

| RSAW bootstrap component | Estimated tokens |
|---|---:|
| `AGENTS.md` | 1,639 |
| `ACTIVE.md` | 432 |
| Active task | 896 |
| **Total** | **2,967** |

`rsaw verify`: **PASS**

> **Claim boundary:** this is a `BOOTSTRAP_CONTEXT_ESTIMATE`. It is not measured provider billing savings, cached-input savings, full-task context reduction, or evidence that engineering quality improved by 91.10%.

V2 closure and task-level continuity/quality measurements remain pending. Read the [full case study](docs/case-studies/desk-code-agent-rsaw-v1-bootstrap.md), browse the [case-study index](docs/case-studies/README.md), or use the [machine-readable result](data/case-studies/desk-code-agent-rsaw-v1.json).

---

## How it works

A session starts small, expands only when the active task requires evidence, validates the result, records the next state, and stops.

```mermaid
flowchart LR
    subgraph BOOT["01 · Bootstrap"]
        direction TB
        R["📦 Repository state<br/>Git · ADRs · tests · evidence"]
        S["✨ Fresh agent session"]
        B["📖 Minimal context<br/>AGENTS.md · ACTIVE.md · active task"]
        R --> S --> B
    end

    subgraph WORK["02 · Bounded work"]
        direction TB
        D{"Need more context?"}
        X["🔎 Read one exact dependency"]
        E["🛠️ Execute one bounded task"]
        D -- "Yes" --> X --> E
        D -- "No" --> E
    end

    subgraph VERIFY["03 · Validate"]
        direction TB
        V["🧪 Targeted validation"]
        C["✅ Closure validation"]
        V --> C
    end

    subgraph HANDOFF["04 · Handoff"]
        direction TB
        H["📝 Update ACTIVE.md"]
        T["⏹ Stop"]
        N["🔄 Next fresh session"]
        H --> T --> N
    end

    B --> D
    E --> V
    C --> H
    N -. "continuity lives in Git" .-> R

    classDef source fill:#0f172a,stroke:#38bdf8,color:#f8fafc,stroke-width:2px;
    classDef session fill:#ecfeff,stroke:#0891b2,color:#164e63,stroke-width:1.5px;
    classDef decision fill:#fff7ed,stroke:#f97316,color:#7c2d12,stroke-width:1.5px;
    classDef work fill:#f5f3ff,stroke:#8b5cf6,color:#4c1d95,stroke-width:1.5px;
    classDef verify fill:#f0fdf4,stroke:#22c55e,color:#14532d,stroke-width:1.5px;
    classDef handoff fill:#fdf2f8,stroke:#ec4899,color:#831843,stroke-width:1.5px;
    classDef stop fill:#f8fafc,stroke:#64748b,color:#0f172a,stroke-width:1.5px;

    class R source;
    class S,B,N session;
    class D decision;
    class X,E work;
    class V,C verify;
    class H handoff;
    class T stop;
```

### The three-file bootstrap

| Artifact | Responsibility | Update pattern |
|---|---|---|
| `AGENTS.md` | Stable policy, safety, build rules, validation, navigation | Rarely |
| `ACTIVE.md` | Tiny current handoff: state, blocker, next action, stop condition | At meaningful boundaries |
| `docs/tasks/<task>.md` | One bounded task and its acceptance criteria | Once per task |

Git, ADRs, tests, reports, and artifacts remain durable evidence—but are read only when the active task needs them.

---

## Five-minute start

### 1. Install

```bash
git clone https://github.com/hanklin9188/repository-state-agent-workflow.git
cd repository-state-agent-workflow
python -m pip install -e '.[dev]'
```

### 2. Add RSAW to an existing repository

```bash
rsaw init /path/to/your-project
cd /path/to/your-project
```

The initializer is conservative: it creates missing workflow files and does not overwrite existing project state unless `--force` is explicitly used.

### 3. Verify the active handoff and footprint

```bash
rsaw verify .
rsaw footprint .
```

### 4. Start a fresh agent session

```text
Work in this repository.

Read only:
1. AGENTS.md
2. ACTIVE.md
3. the active task spec referenced by ACTIVE.md

Execute exactly the active task using progressive disclosure.
Reuse verified repository evidence and do not repeat completed work.
Use targeted validation while iterating and closure validation only when stable.
When complete or blocked, update ACTIVE.md and stop.
```

Or render the role-specific prompt directly:

```bash
rsaw prompt . --role builder
```

---

## Operating model

### Core principles

1. **Repository state is authoritative** — accepted decisions, executable contracts, task state, and evidence outrank old chat history.
2. **One substantial task per session** — stop at completion, closure, a major blocker, reviewer handoff, or decision boundary.
3. **Progressive disclosure** — read exact source, tests, ADRs, reports, and logs only when the active task requires them.
4. **Evidence-gated quality** — smaller context never justifies weaker validation.
5. **Role separation** — builders, reviewers, and decision sessions use different, bounded context.

### Validation tiers

| Tier | Stage | Typical checks |
|---|---|---|
| `V0` | Edit loop | Syntax, lint, one targeted test |
| `V1` | Task stability | Task-specific suite, focused integration |
| `V2` | Task closure | Full relevant tests, package and result checks |
| `V3` | Critical or release work | Fresh reviewer, standards review, spec review |

### Session roles

| Role | Reads | Delivers |
|---|---|---|
| **Builder** | Policy, active state, task, exact dependencies | Implementation and focused evidence |
| **Reviewer** | Fresh context, spec, diff, tests, limitations | Independent correctness and compliance review |
| **Decision** | Evidence checkpoint and governing constraints | Architecture or scientific decision |

For medium-reasoning models, major decisions use two passes: evidence decomposition, then decision synthesis.

---

## CLI

```bash
rsaw init .                            # Add the workflow conservatively
rsaw verify .                          # Validate ACTIVE and task references
rsaw footprint .                       # Estimate fresh bootstrap context
rsaw archive . --label T-042-complete # Archive a meaningful boundary
rsaw prompt . --role builder           # Render a minimal builder prompt
rsaw prompt . --role reviewer          # Render a fresh reviewer prompt
rsaw prompt . --role decision          # Render a decision prompt
```

The CLI is a deterministic guardrail, not an orchestration platform. Markdown and Git remain the canonical state.

---

## Adoption paths

| Setting | Recommended adoption |
|---|---|
| Individual repository | Run `rsaw init`, customize the three core artifacts, add verification to CI |
| Engineering team | Map Issues/Linear/Jira tasks to bounded task contracts; keep the existing tracker |
| Research or ML repository | Add frozen protocols, immutable evidence, explicit authorization, separate execution/review sessions |
| Monorepo | Use stable root policy plus scoped policies and one `ACTIVE.md` per independently operated workstream |

See the [Adoption Guide](docs/adoption-guide.md), [Company Adoption and Governance](docs/company-adoption.md), and [Migration Playbook](docs/migration-playbook.md).

---

## Evaluation and research

RSAW treats lower context as a hypothesis to test—not a quality result by itself. A credible study should measure:

- bootstrap and routine working-set context;
- cached and uncached inputs where provider accounting is available;
- task completion and closure validation;
- repeated work and stale-state errors;
- fresh-session handoff success;
- independent review findings and escaped defects;
- elapsed time and human intervention.

The primary unit should normally be a task or matched task stream, not an individual model call.

Start with:

- [Desk Code Agent V1 Case Study](docs/case-studies/desk-code-agent-rsaw-v1-bootstrap.md)
- [Case Studies Index](docs/case-studies/README.md)
- [Evaluation](docs/evaluation.md)
- [Research Methodology](docs/research-methodology.md)
- [Case Study Template](docs/case-study-template.md)
- [Token Economics](docs/token-economics.md)

The illustrative token-economics examples are not pricing guarantees, and one repository must not be generalized to all models, agents, or organizations.

---

## How RSAW differs

| Approach | Strength | Limitation RSAW addresses |
|---|---|---|
| One long conversation | Rich immediate history | Hidden, growing, stale, difficult to hand off |
| Conversation summary | Compact | Potentially lossy and not independently executable |
| Vector/RAG memory | Flexible retrieval | Retrieval quality and staleness become hidden dependencies |
| Issue tracker only | Strong planning and accountability | Usually lacks agent bootstrap, evidence pointers, and stop contract |
| Agent orchestration framework | Automation and parallelism | Can become another opaque state owner |
| **RSAW** | Explicit, versioned, tool-agnostic continuity | Requires disciplined maintenance of small repository artifacts |

RSAW complements issue trackers, retrieval systems, and orchestrators; it does not require replacing them.

---

## Examples

- [Software feature](examples/software-project/) — streaming parser implementation
- [ML experiment](examples/ml-experiment/) — frozen holdout execution
- [Data pipeline](examples/data-pipeline/) — dual-write migration
- [Research repository](examples/research-repo/) — bounded scientific ticket

Each example contains its own `AGENTS.md`, `ACTIVE.md`, and active task.

---

## Documentation

### Start here

- [Concepts](docs/concepts.md)
- [Architecture](docs/architecture.md)
- [Adoption Guide](docs/adoption-guide.md)
- [Company Adoption and Governance](docs/company-adoption.md)
- [Migration Playbook](docs/migration-playbook.md)

### Operate the workflow

- [Session Lifecycle](docs/session-lifecycle.md)
- [Progressive Disclosure](docs/progressive-disclosure.md)
- [Validation Tiers](docs/validation-tiers.md)
- [Agent Roles](docs/agent-roles.md)
- [Long-Running Work](docs/long-running-work.md)
- [Scientific and ML Workflows](docs/scientific-and-ml-workflows.md)

### Evaluate and extend

- [Desk Code Agent V1 Case Study](docs/case-studies/desk-code-agent-rsaw-v1-bootstrap.md)
- [Case Studies Index](docs/case-studies/README.md)
- [Evaluation](docs/evaluation.md)
- [Research Methodology](docs/research-methodology.md)
- [Token Economics](docs/token-economics.md)
- [Case Study Template](docs/case-study-template.md)
- [Anti-Patterns](docs/anti-patterns.md)
- [FAQ](docs/faq.md)
- [References](docs/references.md)

---

## Status and non-goals

**Status:** Alpha reference implementation. The methodology, templates, examples, verifier, footprint estimator, archive helper, and prompt renderer are usable; broader empirical validation remains open.

RSAW is deliberately **not**:

- an autonomous project manager;
- a model vendor wrapper;
- a replacement for GitHub Issues, Linear, Jira, retrieval, or orchestration;
- an automatic conversation summarizer;
- a database of private conversations;
- a claim that every task fits in one session;
- a reason to weaken tests or human review.

The design stays inspectable: Markdown, Git, deterministic checks, and project-owned evidence.

---

## Contributing, citation, and license

Contributions are welcome, especially measured adoption studies, deterministic workflow checks, monorepo examples, and failure reports. See [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md).

For research use, see [CITATION.cff](CITATION.cff) and cite the specific RSAW version or commit used.

MIT License. See [LICENSE](LICENSE).
