# Validation Tiers

Validation protects the current claim. It is not an invitation to test every hypothetical failure.

| Tier | Boundary | Purpose | Examples |
|---|---|---|---|
| `V0` | Edit loop | Fast local correctness | syntax, lint, exact unit test |
| `V1` | Task checkpoint | Prove the bounded task is stable | focused suite, small integration |
| `V2` | Context epoch / phase closure | Prove the completed coherent phase | full relevant suite once, package check |
| `V3` | Critical claim / release / major fork | Independent challenge | fresh reviewer, scientific/spec review |

## Persistent epoch rule

Several adjacent tasks may each use V1. Run V2 once when the epoch or coherent phase closes, rather than repeating full validation at every task.

## When to add validation

Add a new check only when:

1. an observed defect threatens the next claim; or
2. an explicit contract requires executable coverage.

A legitimate negative scientific result is progress. It does not automatically justify more validator engineering.

## Evidence boundary

Passing tests proves implementation behavior. Measured or production claims still need their own protocol, provenance, data, analysis, and decision rules.
