# Scientific and ML Workflows

Repository-state execution is especially useful when code, protocols, datasets, jobs, and evidence evolve together.

## Mandatory fresh boundaries

### Preregistration

- read design authority;
- freeze protocol and schedule;
- define acceptance, failure, and stopping semantics;
- update the active handoff;
- rotate before execution authorization.

### Formal execution

- read registered protocol, readiness, and authorization;
- execute only authorized work;
- preserve raw evidence;
- validate the terminal contract;
- update ACTIVE;
- rotate.

### Scientific analysis

- start fresh from sealed evidence;
- compare registered expectation with measured result;
- separate facts, inference, and uncertainty;
- stop before implementing a follow-up design.

### Scientific decision

- use a fresh two-pass decision context;
- record options, assumptions, and prospective changes;
- do not retroactively rewrite the prior run.

Persistent engineering workstreams do not remove these independence boundaries.

## Long-running training or benchmarking

Record job ID, code revision, configuration/protocol hash, expected outputs, artifact location, and next review action in `ACTIVE.md`. Stop when waiting is the only remaining action. Use a fresh result-review epoch when the job finishes.

## Evidence state

A software test is not measured evidence. A scientific claim requires protocol, provenance, immutable raw evidence, analysis, and registered interpretation rules.
