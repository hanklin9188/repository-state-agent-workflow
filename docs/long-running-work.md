# Long-Running Work

Long-running work includes CI, builds, benchmarks, training, cloud jobs, deployments, and data processing.

A long-lived workstream does not require a long-lived model context.

## Handoff contract

When the process is the only remaining blocker, record:

- job/run/process ID;
- revision or commit;
- command or protocol;
- expected outputs;
- artifact location;
- completion condition;
- next exact action;
- next role.

Then set the continuation gate to `STOP_REQUIRED` or `ROTATE_REQUIRED` and stop when safe.

## Avoid busy-wait loops

Repeated polling wastes calls and context. Poll only when correctness or safety requires it.

## Result epoch

When the process finishes, use a fresh result-review epoch that reads the job handoff and generated evidence—not the submission conversation.
