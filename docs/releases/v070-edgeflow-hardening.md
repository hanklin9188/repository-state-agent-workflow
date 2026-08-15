# RSAW v0.7 — EdgeFlow-Derived Operator Hardening

RSAW v0.7 promotes the failures observed during a real EdgeFlow v0.6 adoption into permanent runtime and regression requirements.

## Release blockers

The release must prevent or safely contain all of the following:

1. a stale `rsaw` launcher resolving outside the active Python environment;
2. hidden version-specific CLI commands;
3. contradictory Human Gate and continuation state;
4. missing Codex binary or authentication discovered only after operator setup;
5. model-provided source paths being mistaken for supervisor evidence handles;
6. `nextTask.task_id` / `task_spec` compatibility failures;
7. a TUI displaying checkpoint zero when durable checkpoints already exist;
8. repeated ACTIVE updates inflating blank lines beyond the repository budget;
9. partial checkpoint or ACTIVE advancement after post-write verification failure;
10. task-specific GPU access requiring repeated manual sandbox flags;
11. expected PAUSE / COMPLETE states appearing as terminal-process failures in VS Code;
12. unbounded agent rediscovery and tool-output accumulation overwhelming a small compiled envelope;
13. duplicated command lifecycle events inflating tool-call and validation telemetry.

## Required remediation

- Canonical ACTIVE rendering and canonical-budget verification.
- Transactional checkpoint advancement with authority-file rollback.
- Supervisor-owned evidence binding; model source labels are non-authoritative hints.
- Checkpoint-result compatibility for camelCase and snake_case task references.
- Repository-global checkpoint initialization in the Live Runtime Console.
- `rsaw preflight`, `rsaw start`, audited `rsaw gate`, and persistent task sandbox profiles.
- A live per-turn tool budget for calls, output, single-output size, and broad discovery.
- Deduplicated event accounting and explicit tool-output telemetry.
- Operator-safe exit behavior for expected interactive terminal states.

## Release validation

Generated source must pass `py_compile` immediately after materialization, before editable installation, formatting, tests, or packaging. This prevents staging scripts from being mistaken for a valid implementation when their emitted Python source is syntactically invalid.

## Claim boundary

These gates prove runtime behavior and regression coverage. They do not establish a causal token or success-rate improvement. Matched prospective evaluation remains required before publishing efficiency claims.
