# Changelog

All notable changes to the public reference implementation are documented here.

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
