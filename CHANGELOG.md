# Changelog

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
