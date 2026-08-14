# Company Adoption

## Adoption sequence

1. Start in manual repository-state mode.
2. Define stable policy, task/checkpoint contracts, and explicit human gates.
3. Run `rsaw context .` across representative tasks and calibrate budgets.
4. Pilot the Runtime Supervisor with plain logs or the Live Console.
5. Measure checkpoint quality, fresh-input cost, wall time, and intervention rate.
6. Enable strict budgets only after non-inferiority and operational review.

## Governance

RSAW complements issue trackers, CI, review, secrets management, access control, and
incident processes. It does not replace them. Company policy and authorization remain
outside model discretion.

## Recommended rollout metrics

- successful checkpoints;
- fresh input per checkpoint;
- cache reuse ratio with task relevance review;
- rotations and reason codes;
- manual relays and human gates;
- failure recovery and evidence completeness;
- wall time per successful checkpoint.

## Rollback

Pin exact package revisions. Preserve the previous installation source and command.
Never hot-upgrade a supervisor that already owns a repository.
