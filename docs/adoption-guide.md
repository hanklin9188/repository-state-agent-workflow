# Adoption Guide

## 1. Audit current state

Identify where these currently live:

- stable agent instructions;
- current task state;
- task acceptance criteria;
- architecture decisions;
- test and review evidence;
- long-running process state.

Do not create new documents until you know which existing source is authoritative.

## 2. Choose canonical locations

The default layout is:

```text
AGENTS.md
ACTIVE.md
docs/tasks/
docs/decisions/
docs/handoffs/archive/
```

Reuse an existing task directory or ADR convention rather than creating duplicate systems.

## 3. Initialize conservatively

```bash
rsaw init .
```

Review every generated file. The generic template is a starting point, not project truth.

## 4. Move only continuity state

Put stable rules in `AGENTS.md` and immediate continuation state in `ACTIVE.md`.

Do not move complete project history, raw logs, giant result tables, or duplicated design documents into the active handoff.

## 5. Define the first bounded task

Write one task contract with goal, authority, scope, acceptance criteria, validation, evidence, and stop condition.

## 6. Establish validation tiers

Map V0–V3 to the project's real commands. Preserve full closure validation and independent review for critical work.

## 7. Add CI guardrails

```bash
rsaw verify .
rsaw footprint . --max-tokens 15000
```

Treat budgets as engineering guardrails, not universal laws.

## 8. Pilot and measure

Start with one repository or workstream. Measure context, continuity, repeated work, review quality, and human intervention before organization-wide rollout.

See [Company Adoption and Governance](company-adoption.md) for organizational rollout and [Research Methodology](research-methodology.md) for formal evaluation.
