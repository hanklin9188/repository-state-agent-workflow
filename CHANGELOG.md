# Changelog

All notable changes to the public reference implementation are documented here.

## 0.2.0 — Persistent workstreams and context epochs

### Added

- Persistent workstream contracts for multi-day or multi-week project continuity
- Context epochs that may close several adjacent tasks
- Durable task checkpoints separated from context-rotation boundaries
- Explicit `CONTINUE_ALLOWED`, `ROTATE_REQUIRED`, and `STOP_REQUIRED` decisions
- Deterministic continuation safety rules
- `rsaw status`, `rsaw next`, and `rsaw checkpoint`
- Automatic role-aware `rsaw prompt` with fresh/continue modes
- Runner and Analyst role prompts for scientific workflows
- Plug-and-play workstream scaffold created by `rsaw init`
- Context Epoch, Continuation Gate, Getting Started, and migration guides
- English and Traditional Chinese first-screen redesign

### Changed

- Validation V2 now aligns with context-epoch or coherent-phase closure instead of every task
- `ACTIVE.md` records workstream, epoch, gate, next task, and human gate
- Role changes and scientific execution/analysis boundaries force rotation
- Default package description and version updated to 0.2.0

### Compatibility

RSAW 0.1 repositories remain valid. Missing 0.2 workstream metadata defaults to conservative rotation.

### Evidence posture

The existing 91.1% result remains a bootstrap-context estimate from RSAW 0.1. RSAW 0.2 context-epoch savings and quality effects are not yet measured.

## 0.1.0 — Initial public release

### Added

- Repository-State Agent Workflow methodology
- Stable policy, compact active state, task, decision, review, and experiment templates
- `rsaw init`, `verify`, `footprint`, `archive`, and `prompt` commands
- Software, ML, data-pipeline, and research examples
- Company adoption and governance guide
- Research methodology and case-study template
- Bilingual English / Traditional Chinese README
- GitHub issue templates, CI, Dependabot, and social-preview assets

### Evidence posture

This release is an alpha reference implementation. Context-reduction examples are illustrative; broad empirical validation remains future work.
