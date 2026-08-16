# Publishing RSAW

## Release validation

```bash
python -m pip install -e '.[dev]'
ruff format --check .
ruff check .
pytest -q
rsaw verify .
rsaw focus . --json
rsaw compile . --mode FRESH --json
rsaw acceptance . --horizon all --json
python scripts/benchmark_relevance.py
python scripts/check_markdown_links.py .
python -m build
```

Validate Python 3.10, 3.12, and 3.13, then install the wheel in an isolated environment.
Run `rsaw preview .` in a real terminal before publishing a TUI release.

## Repository presentation

- Description: relevance-first repository runtime for long-running coding agents.
- First-screen model: `Truth → Focus → Work → Checkpoint`.
- Keep the relevance architecture and terminal dashboard near the top of the README.
- Update version, metadata, citation, changelog, roadmap, docs, and release assets together.
- Do not leave temporary release workflows on `main`.

## Claim discipline

Synthetic Focus reduction validates selection mechanics only. Do not describe approximate
context counts as provider billing or claim universal token/quality improvement before
matched prospective evidence.
