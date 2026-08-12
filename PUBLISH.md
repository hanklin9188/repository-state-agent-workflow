# Publish This Repository

## Target

- Repository: `hanklin9188/repository-state-agent-workflow`
- Visibility: Public
- License: MIT
- Description: `Repository-backed memory and bounded-session workflow for low-context, high-quality coding agents.`
- Social preview: `docs/assets/social-preview.png`

See [GitHub Presentation Guide](docs/github-presentation.md) and `REPOSITORY_METADATA.json`.

## One-command publication

The publication script validates the tree, creates a local commit if needed, creates the public GitHub repository, pushes `main`, and adds topics.

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
  --description "Repository-backed memory and bounded-session workflow for low-context, high-quality coding agents." \
  --source=. \
  --remote=origin \
  --push
```

## GitHub website alternative

1. Create an empty public repository named `repository-state-agent-workflow`.
2. Do not initialize it with README, license, or `.gitignore`.
3. Run:

```bash
git remote add origin https://github.com/hanklin9188/repository-state-agent-workflow.git
git push -u origin main
```

## Validation before publication

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest -q
rsaw verify .
rsaw footprint . --max-tokens 15000
python scripts/check_markdown_links.py .
```

## Repository settings after push

1. Upload `docs/assets/social-preview.png` as the social preview.
2. Confirm the description and topics from `REPOSITORY_METADATA.json`.
3. Enable Discussions only after there is enough adoption traffic to support them.
4. Keep branch protection proportional to project maturity; require CI for pull requests once collaboration begins.
