# Relevance-First Context

RSAW v0.8 prepares a small, explainable code working set before every fresh model context.
The goal is not to compress everything. The goal is to avoid sending irrelevant repository
content in the first place.

## The four-step model

```text
Truth → Focus → Work → Checkpoint
```

### Truth

Exact authority that must remain unchanged:

- `ACTIVE.md`;
- the active task contract;
- stable governance;
- the bounded Semantic Capsule;
- exact evidence handles when required.

### Focus

A disposable, reproducible repository view:

- SHA-256 content-addressed file index;
- symbols, signatures, imports, and line ranges;
- ranked candidate files;
- a small structural map;
- at most a few exact source excerpts;
- explicit selection reasons and token counts.

### Work

Codex performs semantic engineering using Truth plus Focus. Broad repository discovery is
reserved for a concrete unresolved question.

### Checkpoint

RSAW validates the real diff and commands, then transactionally seals the durable result.
The generated index remains cache, never authority.

## The actual token problem

A small initial prompt can still become an expensive session:

```text
small bootstrap
  → broad repository search
  → large file and tool output
  → another model request with the accumulated transcript
  → more search
  → the transcript is sent again
```

Repeated traffic frequently appears as `cached_input_tokens`. Provider caching may lower
some computation or price, but it does not turn an oversized transcript into a good context
design. RSAW therefore optimizes the number of discovery/model loops and the amount of
model-visible material, not cache ratio alone.

## Deterministic pipeline

1. Enumerate eligible repository files.
2. Reuse unchanged index records by SHA-256 content identity.
3. Extract structure with Python AST and lightweight multi-language fallbacks.
4. Build the task query from exact paths, symbols, current state, tests, and vocabulary.
5. Rank up to a bounded candidate set.
6. Render a small structural map.
7. Select a few exact excerpts under the Focus token ceiling.
8. Reuse unchanged Focus by reference on `CONTINUE`.
9. Force `COMPACT` at the next checkpoint when provider traffic exceeds its ceiling.

## Ideas adapted from established projects

RSAW adopts only the parts that fit a repository-authoritative workflow:

- **Aider:** structural repository map and symbol-aware ranking;
- **Continue:** retrieve more candidates than are finally sent;
- **Cline:** replace expensive transcript history at a safe compaction boundary;
- **OpenHands:** durable history does not need to be visible history;
- **Repomix:** preserve structure before implementation detail.

RSAW deliberately avoids copying their entire stacks. It does not add a graph database,
mandatory embeddings, a second LLM summarizer, or a whole-repository pack to the default
path.

## Selection signals

| Signal | Purpose |
|---|---|
| Exact task path | Highest-confidence implementation target |
| Current Git change | Keep the immediate working set |
| File/path terms | Locate likely modules |
| Symbol names | Find class and function boundaries |
| Content terms | Locate supporting implementation |
| Test relevance | Keep rejecting and regression tests close |
| Direct import | Include nearby dependencies without graph expansion |

`rsaw focus .` reports every selected excerpt and its reasons.

## Default budgets

```json
{
  "enabled": true,
  "mapTokens": 900,
  "focusTokens": 3000,
  "maxSnippets": 5,
  "candidateLimit": 20,
  "snippetLines": 64,
  "maxFileBytes": 200000,
  "maxIndexFiles": 10000,
  "maxProviderInputTokens": 180000,
  "maxCachedInputTokens": 120000
}
```

These values are inspectable engineering guardrails, not universal optima.

## Cache model

The index lives under `.rsaw/cache/` and is excluded from Git authority. Each record is
keyed by content SHA-256. An unchanged second build reuses its record; changing one file
reparses one file.

This local cache is different from provider prompt caching:

```text
local index cache       avoids repeated repository parsing
provider cached input   reports repeated model-visible prefix traffic
```

The second metric should still decline when the context design improves.

## Exclusions

The default index excludes:

- `.rsaw/` runtime, checkpoints, evidence, and cache;
- `artifacts/`;
- virtual environments and build outputs;
- `.env*`, keys, certificates, credentials, and secret-like files;
- files outside the repository root through symlink or path traversal;
- oversized and binary files.

Required governance files remain in Truth and are not duplicated as Focus snippets.

## Continue reuse

On `CONTINUE`, unchanged Task Contract, Semantic Capsule, Exact Evidence, and Focus Context
are represented by content hashes instead of being sent again. RSAW reports the avoided
content as `reusedReferenceTokens` rather than pretending those tokens were newly included.

## Provider-pressure compaction

If a completed turn would normally `CONTINUE` but its latest provider input or cached input
exceeds the configured ceiling, RSAW changes the next lifecycle action to:

```text
COMPACT · PROVIDER_TRAFFIC_PRESSURE
```

This does not erase the cost of the completed turn. It prevents a costly hot transcript from
becoming the base of another turn.

## Safety boundary

Focus is advisory model input. It never replaces:

- allowed-write validation;
- deterministic checkpoint gates;
- evidence handles;
- Human Gates;
- experiment authorization;
- task-scoped sandbox policy;
- external interference checks.

Raw scientific artifacts remain outside the index. A selected excerpt is not scientific
evidence.

## Validation boundary

The deterministic fixture gate requires:

- at least 70% context reduction;
- selection of the target implementation;
- selection of the rejecting test;
- complete second-build index reuse.

The current fixture result is 99.31% mechanism reduction while preserving both targets.
This validates the selection mechanism, not universal provider-token savings or semantic
superiority. Those claims require matched real-workstream evaluation.
