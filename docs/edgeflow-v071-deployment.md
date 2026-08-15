# Deploy RSAW v0.7.1 into EdgeFlow

This procedure upgrades RSAW workflow infrastructure only. It does not authorize or execute an EdgeFlow diagnostic.

## 1. Stop at a durable boundary

Do not replace the active RSAW installation while a Supervisor or Codex worker is live.

```bash
cd ~/StateFT/EdgeFlow_Full_Project_Plan_RTX4080SUPER
ps -ef | grep -E '[r]saw (run|start)|[c]odex exec' || true
test ! -e .rsaw/runtime.lock || cat .rsaw/runtime.lock
```

Continue only after the prior run is durably `PAUSED`, `COMPLETE`, or otherwise stopped and the lock is not live.

## 2. Preserve the current repository boundary

```bash
git status --short > /tmp/edgeflow-pre-rsaw-v071.status
git rev-parse HEAD > /tmp/edgeflow-pre-rsaw-v071.head
sha256sum ACTIVE.md .rsaw/config.json > /tmp/edgeflow-pre-rsaw-v071.sha256
cp ACTIVE.md /tmp/edgeflow-pre-rsaw-v071.ACTIVE.md
cp .rsaw/config.json /tmp/edgeflow-pre-rsaw-v071.config.json
```

Do not reset, clean, restore, or reinitialize the repository.

## 3. Use one canonical RSAW environment

A dedicated virtual environment avoids base/Conda launcher drift:

```bash
python3 -m venv /home/hank/.venvs/rsaw-v071
/home/hank/.venvs/rsaw-v071/bin/python -m pip install --upgrade pip
/home/hank/.venvs/rsaw-v071/bin/python -m pip install --upgrade   "git+https://github.com/hanklin9188/repository-state-agent-workflow.git@v0.7.1"
ln -sfn /home/hank/.venvs/rsaw-v071/bin/rsaw /home/hank/.local/bin/rsaw
export PATH="/home/hank/.local/bin:$PATH"
hash -r
```

Verify identity before touching repository state:

```bash
rsaw --version
/home/hank/.venvs/rsaw-v071/bin/python - <<'PY'
from importlib.metadata import version
import repo_state_agent

assert repo_state_agent.__version__ == "0.7.1"
assert version("repository-state-agent-workflow") == "0.7.1"
print(repo_state_agent.__version__)
PY
```

## 4. Upgrade repository configuration idempotently

```bash
rsaw upgrade . --json
rsaw upgrade . --apply --json
rsaw state normalize . --json
rsaw verify .
```

Schema v4 remains valid. The upgrade must preserve `ACTIVE.md` except for an explicit later normalization or operator action.

## 5. Configure only the reviewed GPU Runner

Keep the repository default at `workspace-write`. Apply the broader sandbox only to the exact reviewed task:

```bash
rsaw sandbox set .   --task E04-GPU-OBSERVABILITY-DIAGNOSTIC-RUNNER-AFTER-COMPATIBILITY-FIX   --mode danger-full-access   --reason "WSL GPU/NVML is visible only across the reviewed Codex device boundary"   --yes   --json
```

Inspect the audit and resolution:

```bash
rsaw sandbox show . --json
rsaw preflight . --json
```

`preflight` must show the exact current task, the audited task override, launcher/Python consistency, and `READY`. A different task must resolve to `workspace-write`.

## 6. Capability smoke is not an experiment

A constrained worker smoke may verify only that the selected sandbox can execute `nvidia-smi` and import PyTorch CUDA. It must not load EdgeFlow models, run the diagnostic, consume a nonce, or produce promotable evidence.

Before any diagnostic, the fresh Runner must separately re-check GPU process inventory. An unrelated workload that could confound utilization observation requires a fail-closed stop.

## 7. Start normal supervised execution

```bash
rsaw start .
```

Expected `PAUSED`, `COMPLETE`, `LIMIT_REACHED`, and `DRY_RUN` states return process exit 0 by default. Automation that needs the internal code uses:

```bash
rsaw run . --strict-exit-codes --no-tui
```

## 8. Clear the broader boundary when it closes

```bash
rsaw sandbox clear .   --task E04-GPU-OBSERVABILITY-DIAGNOSTIC-RUNNER-AFTER-COMPATIBILITY-FIX   --reason "reviewed GPU Runner boundary completed or was abandoned"   --yes   --json
rsaw preflight . --json
```

Confirm the task now resolves to the repository default and preserve the generated operator audit record.

## 9. Rollback

Package rollback does not authorize experiment rollback or retry:

```bash
/home/hank/.venvs/rsaw-v071/bin/python -m pip install --force-reinstall   "git+https://github.com/hanklin9188/repository-state-agent-workflow.git@v0.7.0"
cp /tmp/edgeflow-pre-rsaw-v071.config.json .rsaw/config.json
rsaw verify .
```

Restore `ACTIVE.md` only when the operator explicitly determines that no legitimate post-snapshot state transition occurred.
