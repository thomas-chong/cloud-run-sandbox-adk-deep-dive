# Source: Cloud Run sandbox repository-review evidence

Verified: 2026-07-09

## Exact observed data

- Model: `gemini-3.5-flash`
- Client wall time: 19,098.54 ms
- Detached sandbox launch: 248.97 ms
- Boundary probe: parent canary false; metadata reachable false; public egress reachable false; host application source visible true; sandbox root overlay writable true; dedicated workspace mount writable true.
- Baseline test command: 1 passed, 3 failed; host elapsed 1,944.52 ms.
- Generated candidate: 2,309 bytes; SHA-256 prefix `86e71c85cbf72951`.
- Retest: 4 passed, 0 failed; host elapsed 702.65 ms.
- Snapshot: 5,492,224 bytes.
- Sandbox deletion: return code 0.

## Exact interpretation

A write to the sandbox root succeeded because the named sandbox used `--write`; the write remained in the sandbox's ephemeral overlay and did not mutate the underlying host root. The bind-mounted workspace was intentionally writable. Files baked into the host image were readable, so read-only must not be interpreted as confidential.
