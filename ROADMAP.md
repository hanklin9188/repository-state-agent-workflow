# Roadmap

## 0.3 — Runtime Supervisor

- [x] automatic Codex fresh-context rotation
- [x] resume within bounded epochs
- [x] human/external PAUSE semantics
- [x] terminal COMPLETE state
- [x] provider usage and transition accounting
- [x] failure-safe runtime limits and lock
- [x] manual agent-neutral mode retained
- [ ] prospective controlled adoption study
- [ ] measured quality/non-inferiority analysis

## 0.4 — Runtime Hardening and Interoperability

- detached/background supervisor service with explicit operator controls
- crash-safe resume of supervisor metadata
- optional signed runtime summaries
- richer non-destructive pilot tooling
- first additional agent adapter after Codex behavior is stable
- monorepo and parallel-workstream governance

## Research questions

- When does CONTINUE outperform ROTATE without increasing defects?
- Which task, role, and repository properties predict useful context retention?
- Can token-pressure rotation reduce cost while preserving closure quality?
- How much human relay time does automatic rotation remove?
- Are medium-reasoning models helped disproportionately by cleaner context?
- What is the best metric: total tokens, tokens per closure, or quality-adjusted cost?

## Explicit non-goals

- replacing issue trackers, CI, code review, or access control
- silently bypassing agent sandbox or approval systems
- autonomous authorization of destructive/scientific actions
- hiding failed evidence or automatically retrying formal runs
- claiming universal token or quality improvements without replication
