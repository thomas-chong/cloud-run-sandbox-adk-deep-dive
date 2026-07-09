# Structured infographic content

## Title

A real 19.10-second agent turn — raw stage evidence

## Subtitle

Gemini 3.5 Flash repaired an unsafe `eval`-based rule engine without running repository code in the ADK host.

## Stage 1 — Start

- 248.97 ms
- Detached sandbox
- Egress denied

## Stage 2 — Probe

- Six observed checks
- Parent environment hidden
- Metadata unreachable
- Public egress unreachable
- Host image source readable
- Ephemeral root overlay writable
- Dedicated workspace writable

## Stage 3 — Baseline

- 1,944.52 ms
- 1 passed
- 3 failed

## Stage 4 — Patch

- 2,309 bytes
- SHA-256 prefix: `86e71c85cbf72951`

## Stage 5 — Retest

- 702.65 ms
- 4 passed
- 0 failed

## Stage 6 — Snapshot

- 5,492,224 bytes
- `overlay.tar` created

## Stage 7 — Delete

- Return code 0
- Cleanup succeeded

## Security interpretation

Root write succeeded only in the sandbox's ephemeral `--write` overlay; it did not mutate the host root filesystem.
