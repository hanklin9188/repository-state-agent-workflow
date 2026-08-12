# T-001 — Publish the Initial Public Reference Implementation

## Goal

Publish a polished, bilingual, company-ready and research-ready public repository for Repository-State Agent Workflow.

## Why

The project should communicate both:

- an immediately usable engineering workflow and CLI; and
- an honest research framework for evaluating context, continuity, and quality.

## Blocked By

GitHub repository creation and push access outside this build environment.

## Inputs and Authority

- `AGENTS.md`
- `ACTIVE.md`
- `README.md`
- `README.zh-TW.md`
- `REPOSITORY_METADATA.json`
- `PUBLISH.md`
- source, tests, and CI

## In Scope

- professional English and Traditional Chinese README;
- company adoption and governance guide;
- research methodology and case-study template;
- lightweight `rsaw` CLI;
- generic examples and templates;
- CI, issue templates, Dependabot, social preview;
- local Git commit, bundle, and publication script;
- public repository metadata.

## Out of Scope

- claiming universal token or quality improvements;
- publishing to PyPI;
- building an autonomous project manager;
- replacing GitHub Issues, Linear, Jira, CI, or code review;
- storing private conversations or proprietary logs.

## Acceptance Criteria

- primary README explains the product in the first screen;
- company and research perspectives are explicit;
- all examples remain tool-agnostic;
- CLI tests pass;
- `rsaw verify .` passes;
- bootstrap footprint remains under 15k approximate tokens;
- local Markdown links pass;
- package metadata and CI are valid;
- social preview asset exists;
- public repository publication is reproducible from one script;
- working tree is committed and clean.

## Targeted Tests

```bash
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python -m repo_state_agent verify .
PYTHONPATH=src python -m repo_state_agent footprint . --max-tokens 15000
python scripts/check_markdown_links.py .
```

## Full Closure Validation

```bash
python -m compileall -q src scripts tests
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python -m repo_state_agent verify .
PYTHONPATH=src python -m repo_state_agent footprint . --max-tokens 15000
python scripts/check_markdown_links.py .
git diff --check
```

CI additionally runs Ruff on Python 3.10, 3.12, and 3.13.

## Evidence Expected

- clean local commit;
- passing validation output;
- distributable ZIP, tarball, and Git bundle;
- public GitHub URL after external publication.

## Stop Condition

The prepared tree is clean and validated. Publication remains blocked only if the GitHub repository cannot be created or pushed from the current environment.

## Next Dependency if Complete

Collect the first measured adoption case study for the 0.2 roadmap.
