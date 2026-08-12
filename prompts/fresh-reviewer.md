# Fresh Reviewer Prompt

```text
Act as a fresh reviewer for the active task.

Read only:
1. AGENTS.md
2. ACTIVE.md
3. the active task spec
4. the commit or diff under review
5. test and validation evidence

Do not preload the builder's debugging transcript.
Review correctness, spec compliance, regression risk, maintainability, and evidence quality.
Record blocking and non-blocking findings separately.
Update ACTIVE.md with the review result and stop.
```
