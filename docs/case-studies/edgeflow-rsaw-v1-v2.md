# EdgeFlow — RSAW v1 vs v2 Matched Replay

## Classification

`RETROSPECTIVE_MATCHED_REPLAY_ESTIMATE`

This study reconstructs repository-context traffic for five completed EdgeFlow
tasks under two workflow contracts. It is not provider billing telemetry or a
randomized quality study.

## Matched task stream

1. M0 closure and conservative measurement transition
2. E04 engineering
3. E04 smoke
4. E04 readiness
5. E04 formal-authorization gate

## Results

| Metric | RSAW v1 | RSAW v2 conservative | RSAW v2 delta-only |
|---|---:|---:|---:|
| Matched tasks | 5 | 5 | 5 |
| Fresh sessions / context epochs | 5 | 2 | 2 |
| Estimated repository-context traffic | 53,444 | 20,972 | 19,848 |
| Relative reduction | — | 60.8% | 62.9% |
| Repeated-read reduction | — | 98.1% | 99.0% |

Structured v2 handoff metadata was 20.1% larger than the v1 handoff accounting.
The added metadata encoded the workstream, epoch, next task, role, continuation,
and human gate while reducing repeated large reads.

## Interpretation

For this task stream, grouping tightly coupled E04 Builder work into bounded
epochs substantially reduced estimated repository-context traffic relative to
always-fresh task sessions.

## Claim boundary

- Quality non-inferiority: not causally evaluated.
- Provider billing savings: not evaluated.
- Token method: retrospective repository-context estimate.
- Generality: one workstream; replication is required.

## Next step

RSAW 0.3 records prospective Codex usage, fresh/resumed turns, runtime epochs,
and human pauses. Future EdgeFlow work can compare the replay estimate against
measured runtime accounting.
