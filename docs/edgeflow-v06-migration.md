# EdgeFlow → RSAW v0.6 migration

This procedure upgrades an existing EdgeFlow repository without destroying unrelated worktree state, active experimental evidence, human gates, or one-shot execution authority.

## Preconditions

Do not hot-upgrade a live RSAW Supervisor.

```bash
ps -ef | grep -E '[r]saw run|[c]odex exec' || true
if [ -f .rsaw/runtime.lock ]; then cat .rsaw/runtime.lock; fi
```

The old process must be stopped or safely PAUSED/COMPLETE and the runtime lock released before package replacement or migration.

Do not use:

```text
git reset --hard
git clean -fd
git restore .
git stash
rsaw init --force
```

unless unrelated worktree destruction is explicitly authorized.

## 1. Preserve the pre-v0.6 baseline

Record repository state before migration:

```bash
git status --short
git rev-parse HEAD
git diff --name-only
git diff -- . ':(exclude).rsaw/runtime/**' > /tmp/edgeflow-pre-v06.diff
sha256sum ACTIVE.md .rsaw/config.json 2>/dev/null || true
```

Keep existing `.rsaw/runtime/<run-id>/` evidence. It is useful as the pre-v0.6 baseline and should not be deleted during migration.

## 2. Install exact release

After the real `v0.6.0` tag exists:

```bash
python -m pip install --upgrade \
  "git+https://github.com/hanklin9188/repository-state-agent-workflow.git@v0.6.0"
```

Verify the environment actually imports v0.6:

```bash
python - <<'PY'
from importlib.metadata import version
import repo_state_agent
print("module version       :", repo_state_agent.__version__)
print("distribution version :", version("repository-state-agent-workflow"))
print("module path          :", repo_state_agent.__file__)
assert repo_state_agent.__version__ == "0.6.0"
assert version("repository-state-agent-workflow") == "0.6.0"
PY
```

## 3. Preview migration

```bash
rsaw migrate . --to 0.6 --json
```

The plan must state that `ACTIVE.md` is preserved. Migration changes `.rsaw/config.json`, creates a v0.5 backup, and enables `runtime.v6`; it does not launch Codex or consume an experiment/run authority.

## 4. Apply migration

```bash
sha256sum ACTIVE.md > /tmp/active-before-v06.sha256
rsaw migrate . --to 0.6 --apply
sha256sum ACTIVE.md > /tmp/active-after-v06.sha256
diff -u /tmp/active-before-v06.sha256 /tmp/active-after-v06.sha256
```

The digest must be identical.

## 5. Verify no unrelated EdgeFlow files changed

```bash
git status --short
git diff --name-only
```

Expected migration changes are limited to RSAW configuration/backup state. Existing EdgeFlow implementation, E04 artifacts, schemas, tests, and task documents must retain their pre-migration content unless the operator separately edits them.

## 6. Non-agent validation

Run only deterministic checks first:

```bash
rsaw verify .
rsaw compile . --mode FRESH --json
rsaw run . --dry-run
rsaw acceptance . --horizon all
rsaw preview-v6 . --seconds 8
```

`rsaw run --dry-run` must not require a live Codex turn.

## 7. Existing human/external gates

Migration must not clear an existing gate.

If EdgeFlow is paused on GPU/NVML readiness, formal execution authorization, external results, or another prerequisite, the v0.6 Supervisor must remain PAUSED until that prerequisite is actually satisfied.

A one-shot diagnostic/scientific authority is not consumed by:

- package installation;
- migration;
- compile;
- verify;
- dry-run;
- TUI preview;
- synthetic acceptance.

Only the authorized real Runner task may consume it after readiness passes.

## 8. Start v0.6

Once migration, verification, and the external gate are safe:

```bash
rsaw run . --agent codex
```

or plain mode:

```bash
rsaw run . --agent codex --no-tui
```

The supervised agent is instructed not to mutate `ACTIVE.md` or invoke `advance.py`; the Supervisor owns durable advancement.

## 9. Prospective evaluation

For EdgeFlow, preserve the old v3 runtime summary and compare future workstreams on the required metrics:

```text
attempted checkpoints
successful checkpoints
success rate
total input
cached input
fresh input
input / successful checkpoint
output
fresh contexts
manual relay
true human gates
wall time / successful checkpoint
model calls / successful checkpoint
tool calls / successful checkpoint
compactions
role rotations
repeated input
evidence resend
mean estimated occupancy
recovery rediscovery commands
```

Use matched tasks and separate implementation validation from causal claims.

## Rollback

Package rollback is independent from repository-state rollback.

If v0.6 package behavior must be disabled before it has advanced v0.6 checkpoints:

```bash
cp .rsaw/config.v05.backup.json .rsaw/config.json
python -m pip install --upgrade \
  "git+https://github.com/hanklin9188/repository-state-agent-workflow.git@58924d2db5e5ef39c570ee3dabe9b9b5fcb48ab6"
```

Do not overwrite `.rsaw/state/` or `ACTIVE.md` after accepted v0.6 checkpoints without an explicit recovery procedure; those artifacts are durable authority, not disposable cache.
