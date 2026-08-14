# Changelog

All notable changes to the public reference implementation are documented here.

## 0.4.0 — Live Runtime Console

### Added

- an in-place RSAW Live Terminal dashboard for interactive TTYs, including the
  VS Code Integrated Terminal;
- responsive compact and expanded layouts;
- observable current activity derived from Codex JSON events without exposing
  hidden chain-of-thought;
- workstream, task, role, epoch, checkpoint, transition, human-gate, and runtime
  status in one operator-facing view;
- context-pressure, input, cached-input, fresh-input, output, cache-reuse, and
  rotation-threshold telemetry;
- restrained motion for heartbeat, active work, context-pressure interpolation,
  checkpoint acceptance, and context rotation;
- explicit PAUSED, FAILED, LIMIT_REACHED, and COMPLETE terminal states;
- automatic plain-output fallback for non-TTY, CI, redirected, JSON, quiet, and
  dry-run execution;
- `--tui`, `--no-tui`, and the non-destructive `rsaw preview` command;
- presentation event hooks between the Supervisor, Codex adapter, and TUI;
- focused TUI model, renderer, responsiveness, fallback, and event-isolation
  tests;
- a redesigned README and dedicated Live Terminal UI documentation.

### Preserved

- `CONTINUE`, `ROTATE`, `PAUSE`, and `COMPLETE` lifecycle semantics;
- repository state as the only durable authority;
- existing Codex `exec --json` execution and token accounting;
- bounded context epochs, automatic fresh-thread rotation, human gates,
  single-supervisor locking, and fail-closed verification;
- plain log-oriented behavior for automation and troubleshooting;
- zero intentional model-token overhead from the dashboard itself.

### Claim boundary

The Live Runtime Console is a local observability layer. It does not itself
cause token savings. RSAW's context-lifecycle policy remains the proposed source
of context-efficiency gains, and causal token/quality claims still require
matched prospective evaluation.

## 0.3.0 — Automatic Workstream Runtime

### Added

- `rsaw run . --agent codex` Runtime Supervisor
- automatic CONTINUE and fresh-context ROTATE execution
- explicit PAUSE and COMPLETE semantics
- interactive human-gate resolution without prompt relay
- Codex JSONL thread and token accounting
- `rsaw doctor` compatibility checks
- `rsaw report` runtime-efficiency summaries
- turn, token, transition, and single-supervisor limits
- no-retry failure semantics and repository-state advancement checks
- runtime, Codex adapter, migration, evaluation, and release documentation
- EdgeFlow RSAW v1/v2 matched-replay case study

### Preserved

- Markdown/Git repository authority
- manual and agent-neutral prompt mode
- mandatory fresh scientific/review boundaries
- explicit authorization and destructive-action gates
- immutable failed evidence

### Claim boundary

RSAW 0.3 is implementation- and CI-validated. Prospective token savings and
quality effects remain evaluation questions.

## 0.2.0 — Persistent Workstreams and Context Epochs

### Added

- persistent workstream roadmaps
- bounded context epochs
- durable task checkpoints
- continuation and rotation gates
- role-specific prompts for Builder, Runner, Analyst, Reviewer, and Decision
- matched evaluation methodology

## 0.1.0 — Initial Public Release

### Added

- repository-state methodology
- stable policy, active state, task, review, and experiment templates
- `init`, `verify`, `footprint`, `archive`, and `prompt`
- software, ML, data, and research examples
- initial Desk Code Agent bootstrap case study
