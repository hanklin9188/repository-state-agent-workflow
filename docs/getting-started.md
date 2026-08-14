# Getting Started

RSAW is usable before deep customization. Core mode needs no daemon, database,
hosted memory, or API key. Automatic Runtime mode uses an authenticated local Codex
CLI. Interactive terminals also receive the RSAW Live Runtime Console.

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

## Preview the console

```bash
rsaw preview .
```

Preview is non-destructive: it does not launch Codex or mutate repository state.
Use it to verify colors, responsive layout, and terminal compatibility before a
long run.

## Choose a mode

### Automatic Codex Runtime with Live TUI

```bash
rsaw doctor . --agent codex
rsaw run . --agent codex
```

The supervisor continues or rotates automatically, pauses at real human gates, and
renders live state in an interactive terminal.

```bash
# Plain log-oriented output
rsaw run . --agent codex --no-tui
```

Non-TTY, CI, redirected, JSON, quiet, and dry-run execution automatically uses plain
output.

### Manual agent-neutral Core

```bash
rsaw prompt .
rsaw next .
```

Copy the prompt to any agent and apply the repository gate manually.

## First project setup

Customize four things:

1. stable project policy in `AGENTS.md`;
2. the long-range state machine in the workstream spec;
3. the first bounded task;
4. current and next task, role, and gate in `ACTIVE.md`.

A bounded `## State Machine`, `## Progress`, or `## Phases` section can be displayed
in the console when RSAW can match the current phase unambiguously. RSAW does not
invent phase completion or global percentages.

## First safe pilot

Start with a non-destructive task stream:

```text
contract → implementation → focused test → fresh review → complete
```

Use CONTINUE for the first three Builder tasks, ROTATE for the Reviewer, PAUSE only
for a real gate, and COMPLETE after closure.

Inspect results:

```bash
rsaw report .
rsaw report . --json
```
