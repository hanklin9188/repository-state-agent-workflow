# Long-Running Work Handoff Prompt

```text
The long-running process is now the only blocker.

Record in ACTIVE.md:
- job/run/process ID;
- revision;
- command or protocol;
- expected outputs;
- artifact path;
- completion condition;
- next exact action.

Do not repeatedly poll. Stop when the process can safely continue independently.
```
