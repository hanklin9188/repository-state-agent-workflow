# Publish This Repository

## Target

- Repository: `hanklin9188/repository-state-agent-workflow`
- Visibility: Public
- License: MIT
- Description: `Repository-backed agent workstreams with bounded context epochs, automatic Codex rotation, and a live terminal runtime console.`
- Social preview: `docs/assets/social-preview.png`
- Live console preview: `docs/assets/live-terminal-dashboard.svg`

See [GitHub Presentation Guide](docs/github-presentation.md) and
`REPOSITORY_METADATA.json`.

## One-command publication

The publication script validates the tree, creates a local commit if needed, creates
the public GitHub repository, pushes `main`, and adds topics.

```bash
./scripts/publish_github.sh
```

Prerequisite:

```bash
gh auth login
```

The script refuses to overwrite an existing repository.

## Manual GitHub CLI flow

```bash
git init -b main
git add .
git commit -m "Initial Repository-State Agent Workflow release"

gh repo create hanklin9188/repository-state-agent-workflow \
  --public \
  --description "Repository-backed agent workstreams with bounded context epochs, automatic Codex rotation, and a live terminal runtime console." \
  --source=. \
  --remote=origin \
  --push
```

## Validation before publication

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest -q
rsaw verify .
rsaw footprint . --max-tokens 15000
rsaw preview .
python scripts/check_markdown_links.py .
```

For non-interactive release automation, omit `rsaw preview .` and retain the full
CI suite.

## Repository settings after push

1. Upload `docs/assets/social-preview.png` as the social preview.
2. Confirm the description and topics from `REPOSITORY_METADATA.json`.
3. Keep the Live Console screenshot near the top of the README.
4. Enable Discussions only after adoption traffic can support them.
5. Require CI for pull requests once collaboration begins.
