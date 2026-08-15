# EdgeFlow → RSAW v0.7 Deployment

This guide upgrades an existing EdgeFlow workstream from RSAW v0.6 to v0.7 without deleting uncommitted work, historical runtime evidence, durable checkpoints, human gates, or one-shot execution state.

## What v0.7 changes

v0.7 is an operator/runtime upgrade. It adds:

- a unified CLI and `rsaw start`;
- launcher/Python-environment checks;
- canonical ACTIVE formatting;
- transactional checkpoint advancement and rollback;
- audited Human Gate operations;
- persistent task-specific Codex sandbox profiles;
- live per-turn tool and tool-output budgets;
- repository-global checkpoint display in the TUI;
- compatibility for both camelCase and snake_case task references;
- supervisor-owned evidence binding.

It does **not** rewrite EdgeFlow source code or re-run an experiment during installation, migration, preflight, or preview.

---

## Preconditions

Run from the EdgeFlow repository:

```bash
cd ~/StateFT/EdgeFlow_Full_Project_Plan_RTX4080SUPER
conda activate llama
```

Confirm no RSAW Supervisor or Codex worker owns the repository:

```bash
ps -ef | grep -E '[r]saw run|[c]odex exec' || true

if [ -f .rsaw/runtime.lock ]; then
  cat .rsaw/runtime.lock
fi
```

Do not hot-upgrade a live process. Do not use destructive cleanup commands such as:

```text
git reset --hard
git clean -fd
git restore .
rsaw init --force
```

Preserve `.rsaw/runtime/` and `.rsaw/state/`; they are evidence and durable authority, not disposable cache.

---

## 1. Snapshot the current state

```bash
git status --short > /tmp/edgeflow-pre-rsaw-v07.status
git rev-parse HEAD > /tmp/edgeflow-pre-rsaw-v07.head
sha256sum ACTIVE.md .rsaw/config.json > /tmp/edgeflow-pre-rsaw-v07.sha256
cp ACTIVE.md /tmp/edgeflow-pre-rsaw-v07.ACTIVE.md
cp .rsaw/config.json /tmp/edgeflow-pre-rsaw-v07.config.json
```

No commit, stash, reset, or branch switch is required.

---

## 2. Install the exact release

After `v0.7.0` is published:

```bash
python -m pip install --upgrade \
  "git+https://github.com/hanklin9188/repository-state-agent-workflow.git@v0.7.0"
```

Verify that the package, launcher, and active Python environment agree:

```bash
python - <<'PY'
from importlib.metadata import version
from pathlib import Path
import shutil
import sys
import repo_state_agent

print("module version       :", repo_state_agent.__version__)
print("distribution version :", version("repository-state-agent-workflow"))
print("module path          :", Path(repo_state_agent.__file__).resolve())
print("python               :", Path(sys.executable).resolve())
print("rsaw                 :", shutil.which("rsaw"))

assert repo_state_agent.__version__ == "0.7.0"
assert version("repository-state-agent-workflow") == "0.7.0"
PY
```

`python -m repo_state_agent` is the environment-safe fallback if another `rsaw` launcher shadows the active environment.

---

## 3. Preview and apply the repository migration

Preview only:

```bash
rsaw upgrade . --json
```

The plan must state:

```text
target             0.7
preservesActive    true
v7Enabled          true
```

Apply:

```bash
rsaw upgrade . --apply --json
```

Migration updates `.rsaw/config.json`, creates `.rsaw/config.v06.backup.json`, and leaves `ACTIVE.md` byte-identical.

---

## 4. Canonicalize and verify repository state

```bash
rsaw state normalize . --json
rsaw verify .
```

Canonicalization removes redundant formatting only. It does not change task IDs, role, gates, evidence, stop conditions, or lifecycle decisions. If normalization would leave the repository invalid, RSAW restores the original file.

---

## 5. Run preflight

```bash
rsaw preflight .
```

Preflight checks:

- repository verification;
- active task, role, gate, and durable checkpoint;
- Codex binary and authentication;
- resolved sandbox profile;
- package/launcher/Python consistency;
- configured live tool budgets.

Expected states:

- `READY` — safe to start;
- `PAUSED` — repository is healthy, but a Human Gate remains;
- `FAILED` — fix the reported deterministic prerequisite before execution.

---

## 6. Normal daily use

```bash
rsaw start .
```

`start` performs preflight and then launches the supervised Codex worker with the live TUI. You no longer need to repeat `--agent codex`, `--codex-bin`, or `--tui` in ordinary use.

Useful commands:

```bash
rsaw status .
rsaw report .
rsaw gate show .
rsaw sandbox show .
```

---

## 7. Human Gate workflow

Inspect the gate:

```bash
rsaw gate show . --json
```

After the prerequisite has actually been restored, clear it with an auditable reason:

```bash
rsaw gate clear . \
  --reason "GPU/NVML readiness restored and independently verified" \
  --yes \
  --json
```

RSAW updates the Human Gate and continuation decision atomically, verifies the resulting repository, and records an operator-action artifact under `.rsaw/state/operator-actions/`.

It chooses the continuation policy from the role boundary:

- same role → `CONTINUE_ALLOWED`;
- different role → `ROTATE_REQUIRED`.

Do not clear a scientific, authorization, credential, destructive-operation, or one-shot execution gate merely to make progress.

---

## 8. GPU-visible or privileged task profile

The default sandbox remains `workspace-write`.

For a specific task that genuinely requires direct GPU/NVML visibility:

```bash
rsaw sandbox set . \
  --task current \
  --mode danger-full-access \
  --yes \
  --json
```

Verify:

```bash
rsaw sandbox show . --json
rsaw preflight .
```

Then start normally:

```bash
rsaw start .
```

The override is keyed to the task ID; a later Analyst or Builder task does not inherit another task's broader sandbox unless explicitly configured.

Remove an override when it is no longer required:

```bash
rsaw sandbox clear . --task current --yes --json
```

`danger-full-access` removes Codex sandbox restrictions. Use it only for a reviewed task whose repository contract already authorizes the required operation.

---

## 9. Tool-context protection

Default per-turn limits are:

```json
{
  "maxToolCallsPerTurn": 32,
  "maxToolOutputTokens": 50000,
  "maxSingleToolOutputTokens": 20000,
  "maxBroadDiscoveryCommands": 2,
  "enforce": true
}
```

If a turn exceeds a limit, RSAW requests a process stop and returns a durable `PAUSED` state with `TOOL_BUDGET_EXCEEDED:*`. It does not silently continue accumulating tool output.

Tune these values only with project evidence. A budget abort is a safety/efficiency signal, not proof that the task is incorrect.

---

## 10. Validation after deployment

```bash
rsaw verify .
rsaw compile . --mode FRESH --json
rsaw acceptance . --horizon all --json
rsaw preview . --seconds 8
rsaw preflight . --json
```

Then compare the Git-visible worktree with the pre-upgrade snapshot. Expected migration changes are RSAW configuration/backups/state only; existing EdgeFlow source and experiment artifacts must remain unchanged unless a later supervised task deliberately modifies them.

---

## Rollback

Before v0.7 has accepted a new checkpoint, package/config rollback is:

```bash
cp .rsaw/config.v06.backup.json .rsaw/config.json
python -m pip install --upgrade \
  "git+https://github.com/hanklin9188/repository-state-agent-workflow.git@v0.6.0"
```

After v0.7 has accepted checkpoints, do not replace `.rsaw/state/` or `ACTIVE.md` with older copies without an explicit recovery procedure. Durable authority may have advanced even when package rollback is appropriate.

---

## Recommended EdgeFlow sequence

```bash
# one-time upgrade
python -m pip install --upgrade \
  "git+https://github.com/hanklin9188/repository-state-agent-workflow.git@v0.7.0"
rsaw upgrade . --apply
rsaw state normalize .
rsaw preflight .

# daily use
rsaw start .
```
