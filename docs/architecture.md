# Architecture

```mermaid
flowchart TD
    P[AGENTS.md\nStable policy]
    A[ACTIVE.md\nTiny working memory]
    T[Task spec\nBounded contract]
    D[ADRs / decisions]
    E[Tests / evidence / reports]
    G[Git history]

    S[Fresh session]
    X[Execute one task]
    V[Validation tiers]
    H[Update handoff]

    P --> S
    A --> S
    T --> S
    S -->|on demand| D
    S -->|on demand| E
    S -->|on demand| G
    S --> X --> V --> H --> A
```

## Information classes

| Class | Canonical location | Update frequency | Fresh preload |
|---|---|---:|---:|
| Stable policy | `AGENTS.md` | Low | Yes |
| Current state | `ACTIVE.md` | Every meaningful boundary | Yes |
| Current task | `docs/tasks/` | Per task | Yes |
| Decisions | `docs/decisions/` | At major forks | On demand |
| Evidence/reports | project-defined | Per validation/experiment | On demand |
| Historical handoffs | `docs/handoffs/archive/` | Occasionally | No |
| Raw artifacts | project-defined | Per run | Never by default |

## Authority

A typical authority chain is:

```text
accepted contract / ADR
→ executable schema and tests
→ active task spec
→ ACTIVE.md
→ conversation history
```

Projects should adapt this hierarchy to their domain while avoiding duplicate sources of truth.
