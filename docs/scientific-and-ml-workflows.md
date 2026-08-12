# Scientific and ML Workflows

Repository-state execution is especially useful when code, protocols, datasets, jobs, and evidence evolve together.

## Separate session types

### Preregistration

- read design authority;
- freeze protocol and schedule;
- define acceptance and failure semantics;
- update active handoff;
- stop before execution authorization.

### Formal execution

- read registered protocol, readiness, and authorization;
- execute only authorized work;
- preserve raw evidence;
- validate;
- update active handoff;
- stop.

### Scientific review

Use a fresh two-pass decision session:

1. registered expectation versus measured result;
2. interpretation, competing explanations, and next design.

Do not combine execution and post-hoc follow-up design in one long context.

## Evidence state

A test passing proves software behavior. A measured claim requires its own protocol, provenance, immutable raw evidence, analysis, and decision rules.

## Long-running training

When training is submitted, store the job ID, code revision, configuration hash, expected outputs, and next review action in `ACTIVE.md`. Do not keep an agent session open merely to poll the job.
