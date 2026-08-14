# Roadmap

## 0.1 — Reference implementation

- Repository-backed memory
- Always-fresh bounded sessions
- Conservative scaffold, verifier, footprint, prompt, and archive commands
- Software, ML, data, and research examples
- Adoption and evaluation documentation

## 0.2 — Persistent workstreams

- Context epochs spanning closely coupled tasks
- Durable checkpoints at every task boundary
- Deterministic continuation and rotation gate
- Workstream-aware scaffold, status, next, checkpoint, and prompt commands
- Backward-compatible migration from 0.1
- Scientific and review hard-rotation boundaries

## 0.2 evaluation frontier

- Matched comparison: always persistent vs always fresh vs adaptive epoch
- Tokens per successfully closed task
- Repeated-read and stale-state measures
- Handoff success, reviewer defects, and human interventions
- Context-pressure and rotation-policy sensitivity

## 0.3 — Interoperability

- Optional task-tracker adapters while Markdown/Git remain authoritative
- More role templates for security, release, operations, and scientific review
- Monorepo and parallel-workstream patterns
- Cross-agent and cross-tool handoff demonstrations

## Long-term research questions

- Which repository/task properties predict the value of context retention?
- How should rotation balance re-understanding cost and stale-context risk?
- Can deterministic gates approach learned rotation policies?
- Do medium-reasoning models benefit disproportionately from repository-state continuity?
- Which validation and reviewer patterns prevent quality regression?

## Explicit non-goals

- Building a large autonomous project-management platform
- Owning private conversations or proprietary memory
- Replacing CI, code review, or issue tracking
- Claiming universal token or quality improvements without replicated evidence
