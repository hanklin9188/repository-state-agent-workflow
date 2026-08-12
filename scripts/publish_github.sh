#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-hanklin9188/repository-state-agent-workflow}"
DESCRIPTION="Repository-backed memory and bounded-session workflow for low-context, high-quality coding agents."
TOPICS=(
  coding-agents ai-agents agent-workflow agents-md context-engineering
  developer-tools software-engineering prompt-engineering llm research-tools
)

if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: GitHub CLI (gh) is required." >&2
  echo "Install it, then run: gh auth login" >&2
  exit 1
fi

gh auth status >/dev/null

if gh repo view "$REPO" >/dev/null 2>&1; then
  echo "ERROR: $REPO already exists. Refusing to overwrite it." >&2
  exit 1
fi

if [[ ! -d .git ]]; then
  git init -b main
fi

python scripts/check_markdown_links.py .
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python -m repo_state_agent verify .
PYTHONPATH=src python -m repo_state_agent footprint . --max-tokens 15000

git add .
if ! git diff --cached --quiet; then
  git commit -m "Initial Repository-State Agent Workflow release"
fi

gh repo create "$REPO" \
  --public \
  --description "$DESCRIPTION" \
  --source=. \
  --remote=origin \
  --push

gh repo edit "$REPO" --description "$DESCRIPTION"
for topic in "${TOPICS[@]}"; do
  gh repo edit "$REPO" --add-topic "$topic"
done

echo
printf 'Published: https://github.com/%s\n' "$REPO"
echo "Next: upload docs/assets/social-preview.png in repository Settings > General > Social preview."
