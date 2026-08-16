# T-012 — RSAW v0.8.0 Release Validation

## Objective

Validate and publish the relevance-first runtime without weakening v0.7.1 authority,
sandbox, evidence, checkpoint, or lifecycle guarantees.

## Acceptance

- full test suite passes;
- Ruff format and lint pass;
- repository verification passes;
- Focus selection and budget tests pass;
- provider-pressure compaction tests pass;
- 4 / 16 / 64 acceptance passes;
- Markdown links pass;
- wheel and source distribution build;
- isolated installation passes;
- public tag and release assets match the validated commit.

## Claim boundary

Synthetic reduction validates mechanism only. No universal provider-token or task-success
claim is authorized by this task.
