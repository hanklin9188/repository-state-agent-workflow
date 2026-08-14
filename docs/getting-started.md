# Getting Started

RSAW is designed to be useful before it is customized. There is no service to deploy and no configuration file to learn.

## Install

```bash
python -m pip install git+https://github.com/hanklin9188/repository-state-agent-workflow.git
```

## Initialize an existing repository

```bash
cd /path/to/project
rsaw init .
```

The command creates only missing files. Existing `AGENTS.md`, `ACTIVE.md`, task folders, or project documentation are left untouched unless `--force` is explicit.

## Inspect the generated state

```bash
rsaw verify .
rsaw status .
rsaw footprint .
```

A fresh scaffold starts in bootstrap mode and intentionally requests a rotation before real project work.

## Customize four things

1. Put stable build, safety, validation, and rotation rules in `AGENTS.md`.
2. Replace `W-000` with a real workstream goal and state machine.
3. Replace `T-000` with one actionable task.
4. Update `ACTIVE.md` with the current role, next action, and continuation gate.

## Start the agent

```bash
rsaw prompt .
```

Paste the output into the agent.

## At the first checkpoint

The agent should:

1. persist accepted evidence;
2. close or update the task;
3. activate the next task in `ACTIVE.md`;
4. record `CONTINUE_ALLOWED`, `ROTATE_REQUIRED`, or `STOP_REQUIRED`;
5. run:

```bash
rsaw verify .
rsaw next .
```

## A simple first workstream

```text
W-001 Checkout feature
├── T-001 freeze API contract
├── T-002 implement checkout
├── T-003 integration smoke
├── T-004 readiness
├── T-005 fresh review
└── T-006 release
```

Tasks T-001 through T-004 may fit one Builder context epoch. T-005 must rotate because the role changes to Reviewer.

## Existing RSAW 0.1 repository

No immediate migration is required. A 0.1 `ACTIVE.md` continues to verify and defaults to rotation. Add the workstream, context-epoch, continuation, and next-task sections when ready. See [Migration 0.1 → 0.2](migration-v1-to-v2.md).
