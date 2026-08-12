# Migration Playbook

## Phase 1 — Audit

Classify existing project information:

- stable policy;
- active state;
- tasks;
- decisions;
- evidence;
- historical logs;
- raw artifacts.

## Phase 2 — Choose authority

Define one canonical location for each class. Preserve existing issue trackers and documentation when they already work.

## Phase 3 — Create compact continuation

Create `ACTIVE.md` from current repository facts—not from a conversational summary alone.

## Phase 4 — Refactor global instructions

Keep `AGENTS.md` stable. Move temporary and task-specific content out.

## Phase 5 — Add verification

Run `rsaw verify` and add it to CI.

## Phase 6 — Introduce session boundaries

Start with builder/reviewer separation and one-task sessions. Do not migrate every workflow at once.

## Phase 7 — Measure

Use `rsaw footprint` to compare old and new bootstrap context. Track reliability and repeated-work reduction, not only token counts.
