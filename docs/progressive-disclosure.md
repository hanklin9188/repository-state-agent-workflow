# Progressive Disclosure

## Level 0 — Bootstrap

- `AGENTS.md`
- `ACTIVE.md`
- active task

## Level 1 — Direct implementation

- exact source files being changed;
- exact targeted tests;
- relevant public interface.

## Level 2 — Dependencies

- one ADR;
- one subsystem contract;
- one integration module;
- one prior evidence record.

## Level 3 — Deep debugging or decisions

- full logs;
- historical implementation;
- large artifacts;
- multiple related decisions;
- broad architecture review.

## Rule

A file is not loaded because it is important to the project. It is loaded because it is necessary for the current task.

## Pointers over copies

Prefer:

```text
See docs/reports/T-042-validation.md, commit abc123.
```

over pasting a 500-line report into `ACTIVE.md`.
