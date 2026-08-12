# Contributing

Contributions are welcome when they keep the workflow lightweight, inspectable, and tool-agnostic.

## Principles

- Prefer Markdown, Git, and small deterministic scripts.
- Avoid building a large orchestration framework.
- Do not make one coding agent vendor the source of truth.
- Preserve the separation between stable policy, active state, task specs, decisions, and evidence.
- Add tests for deterministic CLI behavior.

## Development

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest -q
rsaw verify .
```

## Pull requests

A pull request should state:

- the problem;
- the changed workflow contract;
- backward-compatibility implications;
- validation performed;
- whether templates or CLI behavior changed.
