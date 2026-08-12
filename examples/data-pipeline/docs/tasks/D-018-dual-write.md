# D-018 — Dual-Write Events v2 and v3

## Goal
Introduce idempotent dual-write behind a feature flag.

## Acceptance Criteria
- existing v2 output unchanged;
- v3 schema valid;
- retries do not duplicate events;
- rollback disables v3 without affecting v2.
