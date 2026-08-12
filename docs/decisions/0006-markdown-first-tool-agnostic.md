# ADR-0006: Keep Markdown and Git as the canonical workflow state

- Status: Accepted
- Date: 2026-08-12

## Context

Agent workflows can accumulate proprietary databases, opaque summaries, or vendor-specific memory layers. Those systems may be useful, but they can also become another hidden source of truth.

## Decision

The canonical RSAW state remains plain Markdown, Git history, task contracts, and project-owned evidence. The Python CLI provides deterministic verification and scaffolding only.

Integrations may be added, but they must not make a vendor service or generated database the only authoritative state.

## Consequences

- The workflow stays inspectable and portable.
- Teams can use different coding agents.
- Existing issue trackers and retrieval systems can complement RSAW.
- Maintainers must keep small Markdown artifacts accurate.

## Revisit conditions

Revisit if a capability cannot be implemented without a richer storage layer and the proposed layer preserves exportability, auditability, and project ownership.
