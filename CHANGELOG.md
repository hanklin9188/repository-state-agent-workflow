# Changelog

All notable changes to the public reference implementation are documented here.

## 0.7.0 — Operator-Hardened Repository Context Runtime

### Added

- unified `rsaw` / `python -m repo_state_agent` operator CLI;
- `rsaw start` for preflight plus supervised Codex and Live Runtime Console;
- `rsaw preflight` for repository, Codex, authentication, launcher, sandbox, checkpoint, gate, and budget checks;
- audited `rsaw gate show/clear` commands;
- persistent task-specific `rsaw sandbox show/set/clear` profiles;
- `rsaw state normalize` for canonical ACTIVE formatting;
- v0.7 migration and `rsaw upgrade` shortcut;
- live per-turn budgets for tool calls, total tool output, peak single output, and broad repository discovery;
- tool-output, peak-output, budget-abort, and deduplicated broad-discovery telemetry;
- repository-global durable checkpoint initialization in the TUI;
- operator-safe TUI exit behavior for expected PAUSE / COMPLETE states;
- isolated wheel installation and launcher validation in CI;
- v0.7 banner, architecture, lifecycle, terminal-console, EdgeFlow deployment, and release-hardening documentation.

### Fixed

- stale user-local `rsaw` launcher ambiguity is surfaced during preflight;
- source-path evidence references no longer fail as unknown authoritative handles;
- explicit unobserved `EV-*` evidence claims remain rejected;
- Semantic Capsule persists only Supervisor-bound evidence handles;
- `nextTask` accepts both `id` / `taskId` and `task_id`, plus matching spec variants;
- started/completed command lifecycle events are deduplicated for tool and validation accounting;
- per-turn tool budgets reset at every Codex turn;
- repeated ACTIVE updates no longer accumulate blank lines;
- ACTIVE budget checks use canonical representation;
- proposed ACTIVE state is validated before checkpoint commit;
- checkpoint, sidecar, capsule, active pointer, review manifest, and ACTIVE advancement are rolled back together when post-write verification fails;
- Human Gate clearing selects `CONTINUE_ALLOWED` only for same-role work and `ROTATE_REQUIRED` across role boundaries;
- TUI no longer displays checkpoint zero when repository checkpoints already exist;
- task-scoped sandbox configuration removes the need to repeat long GPU-visible run commands.

### Changed

- normal daily use is now `rsaw start .`;
- `rsaw --help` exposes v0.7 commands directly instead of delegating top-level help to the legacy parser;
- `rsaw run --sandbox auto` resolves a task override or the repository default;
- normal interactive TUI use returns a clean shell exit for expected PAUSE / COMPLETE states; `--strict-exit-codes` preserves machine-oriented codes;
- the supervised prompt explicitly prohibits broad rediscovery, bulk file concatenation, unbounded tool output, unchanged-file rereads, model-owned evidence IDs, and noncanonical next-task keys;
- the Live Runtime Console shows durable checkpoint state and live tool/output limits.

### Validation

- generated runtime source must pass `py_compile` before installation;
- Python 3.10, 3.12, and 3.13 run formatting, lint, full pytest, repository/context checks, lifecycle acceptance, documentation links, and package build;
- a separate clean-install job builds the wheel, installs it in an isolated environment, verifies version identity, and starts both CLI entrypoints;
- regression tests cover every EdgeFlow-derived failure listed in `docs/releases/v070-edgeflow-hardening.md`.

### Claim boundary

v0.7 validates runtime safety, operator behavior, migration, packaging, transactional state advancement, and tool-budget enforcement. It does **not** claim a universal causal reduction in provider tokens, wall time, or semantic failure rate before matched prospective evaluation.

## 0.6.0 — Compiled Working Memory Runtime

### Added

- supervisor-owned state advancement: the supervised model no longer needs to edit `ACTIVE.md` or run `advance.py`;
- typed `rsaw.checkpoint-result.v1` final-result contract;
- immutable `rsaw.checkpoint.v6` checkpoint manifests with SHA-256 sidecars;
- durable `.rsaw/state/active.json` compatibility pointer;
- bounded `rsaw.semantic-capsule.v1` warm memory with deterministic field-aware pruning;
- sealed `rsaw.context-envelope.v1` compilation for FRESH, CONTINUE, COMPACT, REVIEW, and RECOVERY modes;
- content-addressed evidence handles and read-if-changed support;
- delta-oriented continuation context;
- deterministic gate checks for ACTIVE ownership, actual changed files, allowed-write scope, validation execution, artifacts, successor readiness, and evidence references;
- `CONTINUE / COMPACT / ROTATE / PAUSE / COMPLETE` lifecycle semantics;
- estimated context occupancy that does not use aggregate provider input as an occupancy proxy;
- bounded `rsaw.review-manifest.v1` for independent reviewers;
- model-call, tool-call, repeated-input, evidence-resend, compaction, rotation, occupancy, and checkpoint-normalized runtime telemetry;
- `rsaw migrate`, `rsaw compile`, `rsaw acceptance`, and `rsaw preview-v6` commands;
- worktree-safe v0.5 → v0.6 migration that preserves `ACTIVE.md` byte-for-byte;
- v0.6 Live Runtime Console showing working-memory, lifecycle, gate, and efficiency state;
- synthetic 4 / 16 / 64-checkpoint lifecycle acceptance command;
- v0.6 architecture, lifecycle, migration, and EdgeFlow integration documentation.

### Changed

- `rsaw` now enters through a compatibility dispatcher. Repositories with `runtime.v6.enabled=true` use the v0.6 supervisor; unmigrated repositories retain the v0.5 runtime path.
- checkpoint persistence is explicitly decoupled from context rotation;
- same-role coherent work defaults to CONTINUE;
- token/context pressure uses COMPACT before ROTATE when cognitive independence is unnecessary;
- role boundaries remain fresh rotations;
- stable governance is referenced rather than resent on CONTINUE envelopes;
- long logs/diffs are represented by durable evidence references rather than unconditional prompt replay.

### Preserved

- repository state as durable authority;
- Codex `exec --json` adapter and sandbox policy;
- single-supervisor lock and fail-closed behavior;
- role-separated scientific/review boundaries;
- PAUSE for human/external gates;
- existing v0.5 CLI and runtime as the migration fallback;
- Rich terminal UI as a non-authoritative local presentation layer.

### Claim boundary

The v0.6 implementation can be validated for deterministic behavior, packaging, migration safety, lifecycle semantics, and synthetic long-horizon mechanics. It does **not** claim measured causal token or semantic-success gains until matched prospective short / medium / long evaluations are run. Promotion targets remain targets, not measured results.

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

Context budgets use approximate token counts. Cache-aware defaults are operating policies, not universal optima. Causal token or quality improvement still requires a matched prospective evaluation.

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
