# W-003 — Runtime Supervisor Release

## Goal

Release and evaluate RSAW 0.3 as a repository-backed persistent workstream
runtime with automatic Codex context rotation.

## State Machine

```text
Implementation
→ deterministic simulation
→ cross-version CI
→ documentation and migration
→ prospective non-destructive pilot
→ measured adoption study
→ release closure
```

## Required Properties

- ROTATE never pauses an otherwise running workstream;
- PAUSE never invents human authority;
- CONTINUE reuses only the current bounded thread;
- every successful turn advances verified repository state;
- failures are terminal and not silently retried;
- role and scientific boundaries remain fresh;
- provider usage is recorded separately from repository-context estimates.

## Validation Budget

V0/V1 for implementation, V2 once for release closure, V3 for prospective
quality claims.

## Human Gates

- authentication or credentials;
- privileged/destructive actions;
- formal scientific authorization;
- publication/release decisions.

## Workstream Stop

The runtime is released, CI is green, documentation is complete, and at least
one prospective pilot is reported with explicit limitations.
