# Daily Builder Prompt

```text
Work in this repository.

Read only:
1. AGENTS.md
2. ACTIVE.md
3. the active task spec referenced by ACTIVE.md

Treat repository state as authoritative over conversation history.
Execute exactly the active task using progressive disclosure.
Reuse verified evidence and do not repeat completed work.
Use targeted validation while iterating and closure validation when stable.
When complete or blocked, update ACTIVE.md and stop.
```
