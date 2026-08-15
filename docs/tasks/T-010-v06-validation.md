# T-010 — RSAW v0.6 release validation

## Objective

Independently validate the v0.6 implementation and release surface without promoting prospective efficiency claims.

## Allowed Writes

- src/**
- tests/**
- docs/**
- README.md
- README.zh-TW.md
- CHANGELOG.md
- ROADMAP.md
- CITATION.cff
- REPOSITORY_METADATA.json
- pyproject.toml
- .rsaw/**
- ACTIVE.md
- AGENTS.md

## Validation

- `ruff check .`
- `pytest -q`
- `rsaw verify .`
- `rsaw compile . --mode FRESH --json`
- `rsaw run . --dry-run`
- `rsaw acceptance . --horizon all`
- `python scripts/check_markdown_links.py .`
- `python -m build`

## Acceptance Criteria

- legacy tests remain green;
- v0.6 tests cover typed result, migration preservation, compiler, evidence, capsule, governor, deterministic gate, and TUI;
- supported Python CI matrix passes;
- package metadata reports 0.6.0;
- the public README distinguishes implementation validation from prospective performance claims;
- migration does not require force-init and preserves `ACTIVE.md`.

## Stop Condition

All validation commands pass and release review finds no blocking correctness or documentation defect.
