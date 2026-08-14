# Getting Started

## Install

```bash
python -m pip install   git+https://github.com/hanklin9188/repository-state-agent-workflow.git
```

Automatic execution also requires an authenticated local Codex CLI.

## Initialize

```bash
cd /path/to/project
rsaw init .
```

Initialization creates only missing files. Customize `AGENTS.md`, `ACTIVE.md`, the
bootstrap workstream, and the first real task before autonomous execution.

## Verify and inspect

```bash
rsaw verify .
rsaw context .
rsaw status .
rsaw next .
rsaw doctor . --agent codex
```

`rsaw context` shows the stable prefix, dynamic authority, hashes, approximate tokens,
and budget status. Use `--strict` only after calibrating the repository budget.

## Preview

```bash
rsaw preview . --seconds 6
```

Preview is non-destructive and does not launch Codex.

## Run

```bash
rsaw run . --agent codex
```

Interactive terminals show the Live Runtime Console. Use `--no-tui` for plain logs.

## Upgrade safety

Do not hot-upgrade a running supervisor. Wait for a durable checkpoint or safe pause,
then update the Python package and rerun verification, context inspection, doctor, and
dry-run checks.
