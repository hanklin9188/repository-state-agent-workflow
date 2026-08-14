# RSAW 0.3 — Runtime Supervisor

RSAW 0.3 executes the context decisions introduced in 0.2.

## Added

- `rsaw run . --agent codex` long-lived supervisor;
- automatic fresh Codex rotation without human prompt relay;
- CONTINUE / ROTATE / PAUSE / COMPLETE runtime semantics;
- interactive human-gate resolution;
- exact Codex JSON token accounting;
- context-pressure and turn-count rotation;
- runtime lock, transition limits, and no-retry failure semantics;
- `rsaw doctor` and `rsaw report`;
- ignored runtime event and summary artifacts.

## Preserved

- Markdown and Git remain project authority;
- manual/tool-neutral mode remains available;
- role and scientific independence boundaries remain fresh;
- human authorization and destructive actions remain explicit;
- failed evidence is not rewritten or automatically retried.

## Claim boundary

The implementation has deterministic unit/integration coverage and CI across
supported Python versions. Prospective token savings and quality effects remain
evaluation questions rather than release claims.
