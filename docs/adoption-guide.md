# Adoption Guide

## Fast path

```bash
python -m pip install git+https://github.com/hanklin9188/repository-state-agent-workflow.git
cd /path/to/project
rsaw init .
rsaw verify .
rsaw status .
rsaw prompt .
```

No service, database, API key, or model integration is required.

## 1. Audit current authority

Identify where stable instructions, current work, task acceptance, decisions, tests, evidence, and long-running state already live. Reuse existing Issue/ADR/task conventions rather than duplicating them.

## 2. Choose one pilot workstream

Start with a feature line, migration, experiment sequence, or release train. Do not reorganize the entire company or monorepo first.

## 3. Keep ACTIVE small

Store only the current frontier, evidence pointers, next action, gate, next task, and role. Keep complete history in existing systems.

## 4. Start conservatively

Use `ROTATE_REQUIRED` at first. Enable `CONTINUE_ALLOWED` for tightly coupled Builder tasks after the next task is independently specified.

## 5. Map validation tiers

Define V0–V3 using real project commands. V2 should run once at context-epoch or phase closure; V3 is reserved for critical independent review.

## 6. Add CI guardrails

```bash
rsaw verify .
rsaw footprint . --max-tokens 15000
```

Treat budgets as local guardrails, not universal laws.

## 7. Measure the pilot

Compare:

- bootstrap and routine working-set context;
- repeated reads and repeated investigation;
- tokens per successfully closed task;
- completion and review quality;
- stale-state errors;
- human interventions;
- elapsed time.

See [Company Adoption](company-adoption.md), [Evaluation](evaluation.md), and [Research Methodology](research-methodology.md).
