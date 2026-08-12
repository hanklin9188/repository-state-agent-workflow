# Validation Tiers

## V0 — Edit loop

Fast feedback:

- parse or compile;
- lint changed file;
- one targeted test;
- deterministic local assertion.

## V1 — Task stability

When the feature appears complete:

- task-specific suite;
- focused integration;
- public-seam negative tests;
- compatibility checks.

## V2 — Ticket closure

Before marking the task complete:

- full relevant test suite;
- repository lint/type checks;
- package/schema/result validation;
- clean diff and worktree checks.

## V3 — Critical or release work

Use a fresh reviewer for:

- standards review;
- spec review;
- security/release checks;
- clean-environment verification;
- scientific review when applicable.

## Why tiers matter

Running the entire test suite after every small edit wastes time and agent context. Running only targeted tests at closure creates false confidence. Tiers preserve both iteration speed and closure quality.
