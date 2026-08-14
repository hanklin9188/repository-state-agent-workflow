# Publishing RSAW

## Release validation

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest -q
rsaw verify .
rsaw context . --strict
rsaw footprint . --max-tokens 15000
rsaw run . --dry-run
rsaw report . --json
python scripts/check_markdown_links.py .
```

Run `rsaw preview .` manually in a real terminal before publishing a UI release.

## Repository presentation

- Description: repository-backed workstreams with cache-aware context planning,
  automatic Codex rotation, and a live terminal runtime console.
- Keep the architecture, context lifecycle, and terminal dashboard visuals near the
  top of the README.
- Update `REPOSITORY_METADATA.json`, `CITATION.cff`, changelog, roadmap, and version
  together.

## Claim discipline

Do not describe approximate context counts as provider billing. Do not claim universal
token or quality improvement before matched prospective evidence.
