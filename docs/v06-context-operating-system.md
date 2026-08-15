# RSAW v0.6 — Context Operating System Runtime

## Scope

v0.6 implements the architecture proposed after the RSAW v3 matched-evaluation failure analysis. The objective is not merely shorter prompts. The objective is lower **total provider input per successful checkpoint** subject to matched semantic-success parity, zero manual relay, and preserved reviewer/scientific independence.

## Failure mechanisms addressed

The v3 analysis identified eight architectural causes:

1. durable persistence was coupled too tightly to context rotation;
2. checkpoint boundaries were treated as context boundaries;
3. the LLM performed deterministic state bookkeeping;
4. aggregate provider input was used as a rotation/pressure proxy;
5. fresh agents received workflow position but insufficient semantic working memory;
6. excessive model/tool loops repeatedly paid stable prefixes;
7. reviewers rediscovered too much repository state;
8. long tool outputs were replayed rather than sealed as bounded evidence.

v0.6 maps each cause to an explicit runtime mechanism.

## Runtime pipeline

```text
1. Durable State Store
        ↓
2. Semantic Capsule
        ↓
3. Context Compiler
        ↓
4. Agent Epoch
        ↓ typed CheckpointResult
5. Deterministic Gate
        ↓
6. Checkpoint / Evidence Sealing
        ↓
7. Token Governor
        ↓
CONTINUE / COMPACT / ROTATE / PAUSE / COMPLETE
```

## Durable state

`.rsaw/state/` is durable repository state, separate from `.rsaw/runtime/` transient process logs.

Recommended layout:

```text
.rsaw/state/
├── active.json
├── capsules/
│   └── <workstream>.json
├── checkpoints/
│   ├── CP-0001.json
│   └── CP-0001.json.sha256
├── evidence/
│   └── EV-*.json
├── envelopes/
│   └── <run>/turn-*.json
└── reviews/
    └── CP-*.json
```

Checkpoint artifacts bind source revision, typed result, gate verdict, governor decision, Context Envelope digest, Semantic Capsule digest, and evidence handles.

## Typed checkpoint result

A supervised agent ends one checkpoint with exactly one `rsaw.checkpoint-result.v1` object. It reports semantic output; it does not advance durable state.

Important fields:

- `outcome`;
- `changedFiles`;
- `validations`;
- `artifacts`;
- `semanticCapsuleDelta`;
- `nextTask` / `followingTask`;
- `nextAction`;
- `stopCondition`;
- requested lifecycle action;
- transition reason;
- human gate.

The final JSON contains facts and decisions, not hidden chain-of-thought.

## Supervisor-owned bookkeeping

When v0.6 supervised mode is active the model must not:

- edit `ACTIVE.md`;
- run `advance.py`;
- self-confirm an ACTIVE mutation;
- choose checkpoint numbers;
- seal its own validation as trusted evidence.

The Supervisor owns those deterministic operations. This removes the administrative inference loops observed in v3 while preserving durable state.

## Deterministic gate

The gate rejects advancement if required invariants fail. Supported checks include:

1. model did not mutate `ACTIVE.md`;
2. result uses the typed schema;
3. actual changed files are reported;
4. declared allowed-write patterns are respected;
5. structured task validation commands were actually observed in the agent event stream;
6. artifacts exist;
7. declared artifact checksum matches;
8. successor task stays inside the repository and exists;
9. Semantic Capsule evidence references bind to known evidence IDs.

Gate failure is fail-closed. The Supervisor does not advance state after a rejection.

## Semantic Capsule

The warm memory schema stores future-useful semantic information that would otherwise be lost on compaction/rotation:

- evidence-backed facts;
- accepted decisions;
- rejected hypotheses plus evidence;
- evidence references;
- unresolved risks;
- high-value code relationships;
- validation state;
- next exact action.

It is not a diary. Field-aware pruning deduplicates semantic IDs, removes resolved risks, replaces superseded records, bounds relation/history lists, converts verbose evidence to references, and applies a token ceiling.

## Context Compiler

The compiler emits `rsaw.context-envelope.v1` for five modes:

- `FRESH`;
- `CONTINUE`;
- `COMPACT`;
- `REVIEW`;
- `RECOVERY`.

### Selection tiers

**Tier A — exact**

Current task contract, acceptance/safety constraints, and bounded critical evidence.

**Tier B — structured semantic state**

Semantic Capsule and current deterministic delta.

**Tier C — references**

Long logs, full diffs, historical transcripts, and other bulky evidence are represented by immutable handles and fetched only when needed.

### Cache-aware ordering

Stable governance remains a cache-stable prefix. A CONTINUE envelope references its existing digest instead of resending the full stable text. Dynamic material remains late.

### Default budgets

```text
target envelope              6,000 tokens
hard envelope               12,000
max exact evidence           7,000
max Semantic Capsule         2,500
max validation summary       1,000
```

Approximate token accounting is explicitly labeled as an estimate.

## Evidence lifecycle

Evidence is content-addressed. Repeated identical evidence maps to the same ID. `read_if_changed` compares the known digest before resending file content.

This makes repeated-input and evidence-resend costs measurable instead of invisible.

## Token Governor

The Token Governor does not interpret cumulative provider input as context occupancy.

Estimated occupancy uses the working-context envelope plus retained semantic/output/tool estimates when provider-native occupancy is unavailable.

Default policy:

```text
< 0.75                     CONTINUE when role/objective remain coherent
0.75–0.85                  COMPACT candidate
>= 0.85                    COMPACT required unless a real rotation boundary exists
role/scientific boundary   ROTATE
human/external gate        PAUSE
stop condition             COMPLETE
```

Turn count is a hard safety ceiling. It is not the normal checkpoint boundary.

## Lifecycle semantics

### CONTINUE

Preserves same-role working cognition. A checkpoint may be sealed and the same thread resumed.

### COMPACT

Efficiency action. Seal the checkpoint and Semantic Capsule, compile a fresh same-role bounded envelope, then continue in a new compact thread.

### ROTATE

Independence action. Use for Builder → Reviewer, Runner → Analyst, major objective/spec changes, and runtime corruption.

### PAUSE

Persists a human/external gate. No busy-poll and no authority bypass.

### COMPLETE

Requires a valid durable stop state.

## Bounded reviewer

At a reviewer boundary the Supervisor emits `rsaw.review-manifest.v1` containing:

- source revision;
- checkpoint and task identity;
- claim;
- acceptance criteria;
- changed files;
- evidence handles;
- known risks;
- bounded review scope.

The Reviewer starts fresh but does not inherit Builder reasoning. Broad repository rediscovery is an explicit escalation.

## Observability

v0.6 records and surfaces:

- total/cached/fresh provider input;
- successful checkpoints;
- model calls;
- tool calls;
- fresh contexts;
- compactions;
- role rotations;
- repeated-input tokens;
- evidence-resend tokens;
- Context Envelope tokens;
- Semantic Capsule tokens;
- estimated occupancy samples;
- deterministic supervisor operations;
- transition reasons.

These metrics support matched short/medium/long evaluation. They do not by themselves prove causal improvement.

## Compatibility

`rsaw` uses a compatibility dispatcher. Existing repositories without `runtime.v6.enabled=true` continue to use the v0.5 execution path. `rsaw migrate . --to 0.6 --apply` enables the v0.6 path while preserving `ACTIVE.md` and backing up the previous config.

## Validation strategy

Implementation validation includes:

- legacy test suite;
- v0.6 schema, capsule, evidence, compiler, governor, gate, migration, and TUI tests;
- Python 3.10 / 3.12 / 3.13 CI;
- `rsaw verify`;
- `rsaw compile --mode FRESH`;
- v0.6 dry-run;
- 4/16/64 synthetic lifecycle acceptance;
- Markdown link audit;
- package build.

Empirical promotion remains separate: matched semantic success must not regress; short-horizon overhead must be bounded; medium and long horizons must demonstrate real provider-token efficiency before strong performance claims are promoted.
