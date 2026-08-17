# RSAW Case Studies

Real-project adoption studies live here. Results are reported conservatively and should distinguish workflow/context measurements from provider billing and full-task quality claims.

## Desk Code Agent

- [RSAW V1 Bootstrap Context Case Study](desk-code-agent-rsaw-v1-bootstrap.md)
  - Status: preliminary V1 adoption evidence
  - `rsaw verify`: PASS
  - Previous-policy deterministic bootstrap lower bound: 33,348 estimated tokens
  - RSAW fresh bootstrap: 2,967 estimated tokens
  - Estimated reduction: 30,381 tokens / 91.10%
  - Measurement label: `BOOTSTRAP_CONTEXT_ESTIMATE`
  - V2 closure and task-level continuity/quality evaluation: pending

Machine-readable summary: [`../../data/case-studies/desk-code-agent-rsaw-v1.json`](../../data/case-studies/desk-code-agent-rsaw-v1.json).

- [RSAW v0.8.0 Matched Workflow Evaluation](desk-code-agent-rsaw-v080-matched.md)
  - Status: post-release matched evidence with post-hoc sensitivity
  - Formal population: 48 attempts / zero harness failures
  - Immutable primary: NO_RSAW 22/24; RSAW v0.8.0 17/24
  - Independently attributed sensitivity: 24/24 versus 24/24
  - RSAW sensitivity effects: 45.39% lower input/success, 24.12% lower uncached
    input/success, 100% fewer broad-discovery commands, and 28.87% higher active
    time/success
  - Disposition: opt-in retrieval-heavy long-workstream pilot only

Machine-readable matched result:
[`../../data/case-studies/desk-code-agent-rsaw-v080-matched.json`](../../data/case-studies/desk-code-agent-rsaw-v080-matched.json).

## Reporting rule

A bootstrap-context reduction is not automatically a provider cost reduction or a quality result. Case studies should report task mix, measurement method, continuity, validation, negative findings, and threats to validity as evidence becomes available.
