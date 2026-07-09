# Infographic rendering prompt

Create a 16:9 technical-schematic infographic using a linear-progression layout and Google Cloud visual language. Use the Google Sans family. White canvas, ample whitespace, seven evenly spaced stage cards connected by one horizontal lifecycle line. Stage colors: Google blue, purple, red, yellow, green, purple, dark green. Include a dark evidence strip at the bottom.

Preserve these exact labels and values:

1. START — 248.97 ms — Detached, egress denied
2. PROBE — 6 checks — env=false · metadata=false · egress=false
3. BASELINE — 1944.52 ms — 1 passed · 3 failed
4. PATCH — 2,309 bytes — 86e71c85cbf72951…
5. RETEST — 702.65 ms — 4 passed · 0 failed
6. SNAPSHOT — 5.49 MB — overlay.tar created
7. DELETE — 0 — cleanup succeeded

Bottom strip:

Observed security boundary
Parent canary hidden · metadata unreachable · public egress unreachable · workspace writable · host image source readable
Root write succeeded only in the sandbox's ephemeral --write overlay; it did not mutate the host root filesystem.

Do not add icons, statistics, claims, or prose that are not listed. Exact numeric and technical text fidelity is mandatory.
