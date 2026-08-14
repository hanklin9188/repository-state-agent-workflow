# W-001 — Checkout Workstream

## Goal

Deliver checkout from implementation through independent review.

## State Machine

```text
T-001 implementation
→ T-002 integration smoke
→ T-003 fresh review
```

## Rotation Policy

T-001 → T-002 may continue. T-002 → T-003 must rotate because the role changes from Builder to Reviewer.
