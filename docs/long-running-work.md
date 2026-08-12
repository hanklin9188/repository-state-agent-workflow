# Long-Running Work

Long-running work includes CI, builds, benchmarks, training, cloud jobs, deployments, and data processing.

## Handoff contract

When the process is the only remaining blocker, record:

- job/run/process ID;
- revision or commit;
- command or protocol;
- expected outputs;
- artifact location;
- completion condition;
- next exact action.

Then stop when the process can safely continue independently.

## Avoid busy-wait loops

Repeated polling wastes model calls and context. Poll only at meaningful intervals required for correctness or safety.

## Results session

When work finishes, use a fresh result-review session that reads the job handoff and generated evidence, not the entire submission session.
