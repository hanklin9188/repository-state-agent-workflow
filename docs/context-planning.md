# Context Planning

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
