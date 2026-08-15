# EdgeFlow GPU Sandbox Incident — Upstream Repair

Date: 2026-08-15  
Upstream release: RSAW v0.7.1  
Scope: RSAW workflow infrastructure only  
Scientific evidence eligibility: **none**

## Incident boundary

An EdgeFlow Runner paused after host GPU visibility and Codex worker visibility diverged. The host WSL environment could see the RTX-class GPU, CUDA, and NVML, while the Codex `workspace-write` worker could not. The worker-side failure was initially misdescribed as an operating-system failure.

The associated capability smoke verified execution-boundary visibility only. It did not run EdgeFlow, consume a formal experiment nonce, authorize a diagnostic retry, modify sealed evidence, or support a scientific claim.

## Public v0.7.0 audit

Public v0.7.0 already provided task sandbox profiles, launcher/Python preflight diagnostics, transactional checkpoint advancement, tool budgets, gate auditing, and synthetic lifecycle acceptance. The incident and final upstream audit exposed these remaining gaps:

1. sandbox resolution occurred once at Supervisor startup rather than before every turn;
2. a broader profile could cross an automatic task transition;
3. explicit CLI `--sandbox` could behave like a run-wide override;
4. sandbox set/clear lacked mandatory non-empty reasons and attributable, content-bound records;
5. operator record tampering was not checked by repository verification;
6. expected non-TUI `PAUSED` states still surfaced process exit 20 by default;
7. launcher identity lacked a direct `--version` command;
8. synthetic rotation was derived from the current phase instead of the next phase.

The locally reported repair commit `bb0b7090a8cb4a0bc91ab80ae8bbddecfe79d7ef` was not reachable from the public GitHub repository during upstream review, so v0.7.1 independently reconstructed and regression-tested the described behavior against public `main`.

## v0.7.1 invariants

- The current `RSAW_TASK_ID` is resolved before every Codex turn.
- Task profiles and explicit CLI sandbox overrides are scoped to one exact task.
- Changing sandbox class forces a fresh context boundary even when the role is unchanged.
- Durable telemetry records turn, task, sandbox, and resolution source.
- The Live Runtime Console displays the effective sandbox boundary.
- `sandbox set` and `sandbox clear` require a non-empty `--reason` and `--yes`.
- Operator records include operator identity, action content, and before/after hashes.
- `rsaw verify` rejects tampered v2 operator records and warns about legacy unbound v1 records.
- A failed verification or audit write restores the prior configuration.
- Expected operator states return shell exit 0 by default in TUI and non-TUI modes; `--strict-exit-codes` retains machine codes.
- 4/16/64 synthetic acceptance derives the next role from the next phase.

## Host-versus-worker diagnosis rule

A worker-side GPU/NVML failure must not be attributed to the host operating system without a differential check:

```text
host capability
       versus
exact worker sandbox capability
```

The comparison is infrastructure evidence only. Formal experiment readiness, interference checks, authorization nonces, and evidence promotion remain separate gates.

## Residual safety boundary

`danger-full-access` is materially broader than `workspace-write`. Keep it scoped to one reviewed task ID, provide an operator reason, re-resolve it every turn, and clear it with another audited reason when the boundary closes.

External GPU workloads remain a fail-closed readiness concern for experiments even when the worker can see the device. RSAW does not terminate or reinterpret unrelated workloads as EdgeFlow evidence.
