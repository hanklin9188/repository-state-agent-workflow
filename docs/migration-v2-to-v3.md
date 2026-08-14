# Migration from RSAW 0.2 to 0.3

RSAW 0.3 keeps the 0.2 workstream, task, epoch, and continuation metadata.
Automatic runtime mode is optional.

## 1. Upgrade

```bash
python -m pip install -U \
  git+https://github.com/hanklin9188/repository-state-agent-workflow.git
```

## 2. Add missing runtime files

Running `rsaw init .` again is conservative: it creates missing
`.rsaw/config.json` and `.rsaw/.gitignore` without overwriting existing policy or
active state.

```bash
rsaw init .
```

Do not use `--force` on a mature repository unless every replacement is
intentional.

## 3. Verify the adapter

```bash
rsaw verify .
rsaw doctor . --agent codex
rsaw run . --dry-run
```

## 4. Update semantics

The existing metadata still works:

| 0.2 metadata | 0.3 runtime action |
|---|---|
| `CONTINUE_ALLOWED` | CONTINUE or safety-forced ROTATE |
| `ROTATE_REQUIRED` | ROTATE automatically |
| `STOP_REQUIRED` | PAUSE |
| Human Gate present | PAUSE |

Add `Decision: COMPLETE` when the workstream is terminal.

## 5. Start supervised mode

```bash
rsaw run . --agent codex
```

A role change now rotates automatically. Only PAUSE requires human/external
input.

## Safe rollout

1. Run `--dry-run`.
2. Use a small non-destructive workstream.
3. Keep `approve_for_me` false.
4. Review `.rsaw/runtime/*/summary.json`.
5. Expand to formal/research work only after role boundaries and human gates are
   represented correctly in `ACTIVE.md`.

Manual mode remains available at every stage.
