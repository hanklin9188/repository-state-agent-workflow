# Deploy RSAW v0.8.0 into EdgeFlow

This procedure upgrades workflow infrastructure and enables relevance-first context. It does not authorize or execute an EdgeFlow diagnostic.

## 1. Stop at a durable boundary

Do not replace RSAW while a Supervisor or Codex worker is live.

```bash
cd ~/StateFT/EdgeFlow_Full_Project_Plan_RTX4080SUPER

ps -ef | grep -E '[r]saw (run|start)|[c]odex exec' || true

test ! -e .rsaw/runtime.lock || cat .rsaw/runtime.lock
```

Continue only after the previous run is durably stopped and no live lock owner exists.

## 2. Preserve the current boundary

```bash
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup="/tmp/edgeflow-rsaw-v080-$stamp"
mkdir -p "$backup"

git status --short > "$backup/git-status.txt"
git rev-parse HEAD > "$backup/head.txt"
sha256sum ACTIVE.md .rsaw/config.json > "$backup/state.sha256"
cp ACTIVE.md "$backup/ACTIVE.md"
cp .rsaw/config.json "$backup/config.json"
command -v rsaw > "$backup/rsaw-launcher.txt" 2>&1 || true
readlink -f "$(command -v rsaw)" > "$backup/rsaw-launcher-resolved.txt" 2>&1 || true

printf 'Backup: %s\n' "$backup"
```

Do not reset, clean, restore, stash, or reinitialize the repository.

## 3. Install one canonical RSAW environment

```bash
python3 -m venv /home/hank/.venvs/rsaw-v080

/home/hank/.venvs/rsaw-v080/bin/python \
  -m pip install --upgrade pip

/home/hank/.venvs/rsaw-v080/bin/python \
  -m pip install --upgrade --force-reinstall \
  "git+https://github.com/hanklin9188/repository-state-agent-workflow.git@v0.8.0"
```

Before switching the launcher:

```bash
/home/hank/.venvs/rsaw-v080/bin/rsaw --version
/home/hank/.venvs/rsaw-v080/bin/python -m repo_state_agent --version

/home/hank/.venvs/rsaw-v080/bin/python - <<'PY'
from importlib.metadata import version
import sys
import repo_state_agent

print("sys.prefix           :", sys.prefix)
print("sys.base_prefix      :", sys.base_prefix)
print("module version       :", repo_state_agent.__version__)
print("distribution version :", version("repository-state-agent-workflow"))

assert sys.prefix == "/home/hank/.venvs/rsaw-v080"
assert sys.prefix != sys.base_prefix
assert repo_state_agent.__version__ == "0.8.0"
assert version("repository-state-agent-workflow") == "0.8.0"
PY
```

All version checks must report `0.8.0`. Use `sys.prefix`, not the resolved Python
symlink target, to verify virtual-environment ownership.

## 4. Verify existing operator records before migration

Use the new binary by absolute path:

```bash
/home/hank/.venvs/rsaw-v080/bin/rsaw verify . \
  | tee "$backup/rsaw-v080-verify-before.txt"

/home/hank/.venvs/rsaw-v080/bin/rsaw sandbox show . --json \
  | tee "$backup/rsaw-v080-sandbox-before.json"

/home/hank/.venvs/rsaw-v080/bin/rsaw preflight . --json \
  | tee "$backup/rsaw-v080-preflight-before.json"
```

Legacy `rsaw.operator-action.v1` records remain readable with a warning. Do not rewrite or delete historical operator records merely to remove the warning.

## 5. Switch the canonical launcher

```bash
mkdir -p /home/hank/.local/bin

ln -sfn \
  /home/hank/.venvs/rsaw-v080/bin/rsaw \
  /home/hank/.local/bin/rsaw

export PATH="$HOME/.local/bin:$PATH"
hash -r

command -v rsaw
readlink -f "$(command -v rsaw)"
rsaw --version
```

Expected resolved launcher:

```text
/home/hank/.venvs/rsaw-v080/bin/rsaw
```

## 6. Upgrade repository configuration

Preview first:

```bash
rsaw upgrade . --json
```

Apply and normalize:

```bash
rsaw upgrade . --apply --json
rsaw state normalize . --json
rsaw verify .
```

The migration:

- moves the configuration to schema 5;
- adds `runtime.relevance` defaults;
- writes `.rsaw/config.v071.backup.json` when needed;
- preserves `ACTIVE.md` byte-for-byte before explicit normalization;
- does not call Codex or execute EdgeFlow.

Inspect the diff:

```bash
git diff -- ACTIVE.md .rsaw/config.json
```

## 7. Build and inspect the Focus Context

The first build parses eligible files. Later builds reuse content-hash cache entries.

```bash
rsaw focus . --rebuild --json \
  | tee "$backup/rsaw-v080-focus-first.json"

rsaw focus . --json \
  | tee "$backup/rsaw-v080-focus-cached.json"
```

Expected properties:

- the active E04 Runner implementation and rejecting tests are selected;
- `ACTIVE.md`, `AGENTS.md`, and the task contract are not duplicated as code snippets;
- `.rsaw/runtime`, raw evidence, and `artifacts/` are not indexed;
- the second build reports predominantly cache hits;
- map and focus tokens remain within configured ceilings.

To inspect exact excerpts and reasons without starting Codex:

```bash
rsaw focus . --show-content
```

## 8. Preserve the exact GPU sandbox boundary

The repository default must remain `workspace-write`. The reviewed Runner may retain its exact task override:

```bash
rsaw sandbox show . --json
```

For the current task, the expected resolution is:

```text
Task    E04-GPU-OBSERVABILITY-DIAGNOSTIC-RUNNER-AFTER-COMPATIBILITY-FIX
Mode    danger-full-access
Source  task override
```

Do not create a second sandbox-set record if the correct override already exists.

A different task must resolve to `workspace-write` unless it has its own independently reviewed override.

## 9. Final preflight

```bash
rsaw verify .
rsaw focus . --json
rsaw preflight . --json
rsaw next .
```

Expected state:

```text
verify             PASS
preflight          READY
current task       exact post-compatibility-fix Runner
sandbox            danger-full-access from task override
focus              enabled and within budget
continuation       CONTINUE_ALLOWED
next               CONTINUE, same epoch, Runner
```

Stop here after deployment. Do not automatically start the diagnostic.

## 10. Re-check external GPU interference before execution

```bash
nvidia-smi

nvidia-smi \
  --query-compute-apps=pid,process_name,used_gpu_memory \
  --format=csv,noheader
```

An unrelated `VLLM::EngineCore` or other workload that can confound utilization observation requires a fail-closed stop. RSAW must not terminate that process automatically or reinterpret it as EdgeFlow activity.

Only after the fresh Runner independently passes all readiness gates should the operator run:

```bash
rsaw start .
```

## 11. Observe the new token controls

During execution, the Live Runtime Console shows:

- durable checkpoint;
- task and sandbox;
- Context Envelope tokens;
- Focus tokens and snippet count;
- Semantic Capsule size;
- provider input, cached input, and fresh input;
- tool-call and tool-output budgets.

After a durable stop:

```bash
rsaw report . --json \
  | tee "$backup/rsaw-v080-runtime-report.json"
```

Evaluate at least:

```text
input tokens / successful checkpoint
cached input / successful checkpoint
fresh input / successful checkpoint
tool calls / successful checkpoint
broad discovery commands
focus tokens and snippet count
focus cache hit/miss counts
successful checkpoint rate
```

## 12. Clear the broader sandbox when the Runner boundary closes

```bash
rsaw sandbox clear . \
  --task E04-GPU-OBSERVABILITY-DIAGNOSTIC-RUNNER-AFTER-COMPATIBILITY-FIX \
  --reason "reviewed GPU Runner boundary completed or was abandoned" \
  --yes \
  --json

rsaw verify .
rsaw preflight . --json
```

## 13. Rollback

Package rollback does not authorize experiment rollback or retry.

```bash
/home/hank/.venvs/rsaw-v080/bin/python \
  -m pip install --force-reinstall \
  "git+https://github.com/hanklin9188/repository-state-agent-workflow.git@v0.7.1"

cp "$backup/config.json" .rsaw/config.json
rsaw verify .
```

Restore `ACTIVE.md` only when the operator has established that no legitimate post-snapshot transition occurred.

## Scientific boundary

This deployment does not:

- authorize a formal E04 retry;
- reuse a consumed formal nonce;
- execute the separate diagnostic;
- consume the remaining diagnostic authority;
- modify sealed evidence;
- load an EdgeFlow model;
- promote Focus Context or capability smoke into scientific evidence;
- establish a token-efficiency claim without matched evaluation.
