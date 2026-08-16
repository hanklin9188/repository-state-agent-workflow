# T-013 — RSAW v0.8.0 Matched Prospective Study

## Objective

Compare direct Codex, RSAW v0.7.1, and RSAW v0.8.0 on matched real workstreams.

## Fixed controls

- same model and reasoning setting;
- same starting repository revision;
- same task and acceptance criteria;
- same tool and sandbox availability;
- independent semantic-success adjudication.

## Primary metrics

- successful checkpoint rate;
- total, cached, and fresh input per successful checkpoint;
- model and tool calls per successful checkpoint;
- broad-discovery commands;
- tool-output traffic;
- wall time;
- manual relay and true Human Gates;
- recovery accuracy and authority violations.

## Stop condition

A matched ledger supports or rejects v0.8 promotion claims without relying on synthetic
context reduction alone.
