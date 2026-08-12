# T-042 — Streaming Parser

## Goal
Support incremental streamed input without buffering the full payload.

## Requirements
- deterministic;
- UTF-8 safe;
- preserve public API;
- handle empty and malformed chunks.

## Acceptance Criteria
- split ASCII token;
- split multi-byte UTF-8 code point;
- empty chunk;
- malformed input;
- large stream;
- existing parser tests pass.

## Stop Condition
Implementation and closure validation complete.
