# RSAW Context Policy

## Stable Prefix

Keep stable policy before dynamic task state. Stable files should change rarely and
retain a deterministic fingerprint.

## Dynamic Authority

`ACTIVE.md`, the active task, and explicitly required evidence form the dynamic
suffix. Do not preload the repository tree.

## Continue

When the supervisor resumes the same thread, reread dynamic authority only. Reload
the stable prefix only when its fingerprint changes.

## Rotate

Rotate at role/scientific boundaries, hard token pressure, fresh-input pressure,
or low cache reuse near the soft threshold.

## Measurement

Track total input, cached input, fresh input, output, checkpoints, epochs, and
rotations. Optimize fresh input per successful checkpoint, not cache hits alone.
