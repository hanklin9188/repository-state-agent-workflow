# T-007 — Live Runtime Console Prospective Pilot

## Objective

Run one bounded, non-destructive prospective RSAW workstream with the Live Terminal
Console and record operator, lifecycle, token, checkpoint, and quality outcomes.

## Measurements

- attempted and successful checkpoints;
- runtime epochs, fresh turns, and resumed turns;
- CONTINUE, ROTATE, PAUSE, and COMPLETE counts;
- total, cached, fresh, and output tokens;
- tokens per successful checkpoint;
- manual relay and true human-gate counts;
- wall time per successful checkpoint;
- operator-visible UI defects or ambiguity.

## Constraints

- freeze the RSAW revision before the run;
- do not alter lifecycle policy during measurement;
- use independent checkpoint validation;
- do not infer causal improvement from a single pilot.

## Stop Condition

A reproducible pilot report is committed with raw runtime evidence and explicit
limitations.
