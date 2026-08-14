# Getting Started

RSAW is usable before deep customization. No daemon, database, hosted memory, or
API key is required for Core mode. Automatic Runtime mode uses an authenticated
local Codex CLI.

## Install

```bash
python -m pip install \
  git+https://github.com/hanklin9188/repository-state-agent-workflow.git
```

## Initialize

```bash
cd /path/to/project
rsaw init .
```

The command creates only missing files.

## Inspect

```bash
rsaw verify .
rsaw status .
rsaw footprint .
rsaw run . --dry-run
```

## Choose a mode

### Automatic Codex Runtime

```bash
rsaw doctor . --agent codex
rsaw run . --agent codex
```

The supervisor continues or rotates automatically and pauses at human gates.

### Manual Agent-neutral Core

```bash
rsaw prompt .
rsaw next .
```

Copy the prompt to any agent and use the repository gate manually.

## First project setup

Customize four things:

1. stable project policy in `AGENTS.md`;
2. the long-range state machine in the workstream spec;
3. the first bounded task;
4. current and next task, role, and gate in `ACTIVE.md`.

## First safe pilot

Start with a non-destructive task stream:

```text
contract → implementation → focused test → fresh review → complete
```

Use CONTINUE for the first three Builder tasks, ROTATE for the Reviewer, PAUSE
only for a real gate, and COMPLETE after closure.

Inspect results:

```bash
rsaw report .
```
