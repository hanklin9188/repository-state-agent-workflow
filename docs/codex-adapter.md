# Codex Runtime Adapter

The automatic adapter uses local Codex CLI structured execution:

```text
fresh     codex exec --json ... -
continue  codex exec --json ... resume <thread-id> -
```

Prompts are passed through stdin. The adapter records thread IDs, terminal events, and
provider-emitted usage. It never enables the dangerous sandbox bypass.

## Context integration

RSAW sets an ordered prompt contract and passes the stable-prefix fingerprint in the
worker environment. Continued prompts avoid asking Codex to reread unchanged stable
policy; fresh prompts provide the complete minimal read order.

## Observability

Structured events feed both durable JSONL and the best-effort Live Console. Event-sink
exceptions are isolated from the worker.

## Requirements

- `codex` on `PATH` or `--codex-bin`;
- authenticated CLI;
- support for `exec`, `--json`, resume, and last-message output;
- a verified RSAW repository.

Check with:

```bash
rsaw doctor . --agent codex
```
