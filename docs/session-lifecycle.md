# Session Lifecycle

```mermaid
flowchart TD
    N[New session] --> R[Read AGENTS + ACTIVE + active task]
    R --> Q{Need more context?}
    Q -->|Yes| D[Read exact dependency]
    Q -->|No| X[Execute]
    D --> X
    X --> V0[V0 targeted validation]
    V0 --> C{Task stable?}
    C -->|No| X
    C -->|Yes| V2[V1/V2 closure validation]
    V2 --> U[Update ACTIVE]
    U --> S[Stop]
```

## Recommended session boundaries

Start a fresh session after:

- task completion;
- closure verification;
- a large debugging episode;
- builder-to-reviewer transition;
- a major design decision;
- long-running work handoff;
- a significant change in the governing hypothesis or specification.

The boundary is a quality mechanism, not merely a token-saving trick. It removes obsolete context and forces explicit handoff state.
