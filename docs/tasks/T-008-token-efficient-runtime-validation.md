# T-008 — Token-Efficient Runtime Validation

## Goal

Independently validate the RSAW 0.5 implementation and public presentation.

## Acceptance Criteria

- legacy and nested config parse correctly;
- context plans are ordered, deduplicated, local, fingerprinted, and budgeted;
- fresh and continuation prompts preserve the intended read contract;
- rotation reason precedence is deterministic;
- existing supervisor, Codex, and TUI tests remain green;
- `rsaw context . --strict` passes for this repository;
- README diagrams and local Markdown links are valid;
- no causal token-saving claim is promoted.

## Validation

```bash
ruff check .
pytest -q
rsaw verify .
rsaw context . --strict
rsaw run . --dry-run
rsaw report . --json
python scripts/check_markdown_links.py .
```

## Stop Condition

All implementation and documentation checks pass and findings are recorded.
