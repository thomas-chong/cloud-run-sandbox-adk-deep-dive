#!/usr/bin/env python3
# ruff: noqa: E501
"""Generate a guided latency histogram plus aligned raw-run dot plot."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "assets" / "evidence" / "latency.json"
OUT = ROOT / "assets" / "latency-results.html"

data = json.loads(EVIDENCE.read_text())
response = data["events"][1]["content"]["parts"][0]["functionResponse"]["response"]
raw = sorted(float(value) for value in response["raw_ms"])

x_min, x_max = 400.0, 480.0
plot_left, plot_right = 120.0, 1390.0
plot_width = plot_right - plot_left
hist_top, baseline = 125.0, 380.0
count_max = 15


def x(value: float) -> float:
    return plot_left + (value - x_min) / (x_max - x_min) * plot_width


bins = [(start, start + 10) for start in range(400, 480, 10)]
counts = []
for start, end in bins:
    count = sum(start <= value < end for value in raw)
    if end == 480:
        count = sum(start <= value <= end for value in raw)
    counts.append(count)

horizontal_grid = []
for count in (0, 5, 10, 15):
    y = baseline - count / count_max * (baseline - hist_top)
    horizontal_grid.append(
        f'<line x1="{plot_left}" y1="{y:.1f}" x2="{plot_right}" y2="{y:.1f}" class="hgrid"/>'
        f'<text x="{plot_left - 18}" y="{y + 5:.1f}" class="gridLabel">{count}</text>'
    )

vertical_grid = []
for tick in range(400, 481, 10):
    px = x(tick)
    vertical_grid.append(
        f'<line x1="{px:.1f}" y1="95" x2="{px:.1f}" y2="570" class="vgrid"/>'
        f'<text x="{px:.1f}" y="420" class="axis">{tick}</text>'
    )

bars = []
for (start, end), count in zip(bins, counts, strict=True):
    left = x(start) + 9
    width = x(end) - x(start) - 18
    height = count / count_max * (baseline - hist_top)
    top = baseline - height
    bars.append(
        f'<rect x="{left:.1f}" y="{top:.1f}" width="{width:.1f}" height="{height:.1f}" rx="9" class="bar"/>'
        f'<text x="{left + width / 2:.1f}" y="{top - 10:.1f}" class="count">{count}</text>'
    )

bucket_rows: defaultdict[int, int] = defaultdict(int)
dots = []
for value in raw:
    bucket = min(7, max(0, int((value - 400) // 10)))
    row = bucket_rows[bucket] % 5
    bucket_rows[bucket] += 1
    y = 500 + row * 16
    dots.append(
        f'<circle cx="{x(value):.1f}" cy="{y}" r="5" class="dot"><title>{value:.3f} ms</title></circle>'
    )

markers = []
for label, value, color, y_offset in (
    ("P50", response["p50_ms"], "#1967d2", 70),
    ("P95", response["p95_ms"], "#b06000", 94),
    ("P99 / max", response["p99_ms"], "#c5221f", 70),
):
    px = x(float(value))
    width = 130 if label != "P99 / max" else 160
    left = max(plot_left, min(plot_right - width, px - width / 2))
    markers.append(
        f'<line x1="{px:.1f}" y1="95" x2="{px:.1f}" y2="570" stroke="{color}" class="percentile"/>'
        f'<rect x="{left:.1f}" y="{y_offset - 22}" width="{width}" height="27" rx="13.5" fill="white" stroke="{color}"/>'
        f'<text x="{left + width / 2:.1f}" y="{y_offset - 4}" text-anchor="middle" class="marker" fill="{color}">{label} {float(value):.1f} ms</text>'
    )

html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Guided Cloud Run sandbox latency</title><style>
*{{box-sizing:border-box}}html,body{{margin:0;width:1600px;height:900px;overflow:hidden}}body{{font-family:'Google Sans','Google Sans Flex',Arial,sans-serif;background:#f8fafd;color:#202124}}.c{{padding:44px 58px}}h1{{font-size:42px;margin:0;letter-spacing:-1.1px}}.sub{{font-size:19px;color:#5f6368;margin-top:8px}}.cards{{display:flex;gap:16px;margin:24px 0 8px}}.card{{background:white;border:1px solid #dadce0;border-radius:16px;padding:15px 20px;min-width:180px}}.v{{font-size:28px;font-weight:720;color:#1967d2}}.k{{font-size:12px;font-weight:750;letter-spacing:.8px;color:#5f6368}}svg{{width:1484px;height:610px}}.hgrid{{stroke:#cbd2d9;stroke-width:1}}.vgrid{{stroke:#e1e6eb;stroke-width:1}}.gridLabel{{font:600 13px 'Google Sans',Arial;fill:#5f6368;text-anchor:end}}.axis{{font:600 14px 'Google Sans',Arial;fill:#5f6368;text-anchor:middle}}.bar{{fill:#4285f4;opacity:.9}}.count{{font:720 16px 'Google Sans',Arial;fill:#202124;text-anchor:middle}}.dot{{fill:#1967d2;stroke:white;stroke-width:2;opacity:.88}}.percentile{{stroke-width:2;stroke-dasharray:7 6;opacity:.76}}.marker{{font:720 12px 'Google Sans',Arial}}.section{{font:750 13px 'Google Sans',Arial;fill:#3c4043;letter-spacing:.7px}}.guide{{font:500 14px 'Google Sans',Arial;fill:#5f6368}}.axisTitle{{font:720 14px 'Google Sans',Arial;fill:#3c4043;text-anchor:middle}}.foot{{font:500 13px 'Google Sans',Arial;fill:#5f6368}}.callout{{fill:#e8f0fe;stroke:#a8c7fa}}
</style></head><body><div class="c"><h1>Sandbox lifecycle latency — 30/30 successful</h1><div class="sub">One warm Cloud Run instance · <code>sandbox do -- /bin/true</code> · create + exec + delete</div><div class="cards"><div class="card"><div class="k">P50</div><div class="v">428.347 ms</div></div><div class="card"><div class="k">P95</div><div class="v">455.854 ms</div></div><div class="card"><div class="k">P99</div><div class="v">470.934 ms</div></div><div class="card"><div class="k">MEAN</div><div class="v">431.902 ms</div></div><div class="card"><div class="k">RANGE</div><div class="v">408.9–470.9</div></div></div>
<svg viewBox="0 0 1484 610">
<text x="120" y="28" class="section">HOW TO READ IT</text><rect x="120" y="40" width="16" height="12" rx="3" class="bar"/><text x="145" y="51" class="guide">bars = runs per 10 ms interval</text><circle cx="400" cy="46" r="5" class="dot"/><text x="415" y="51" class="guide">dots = individual runs on the same x-axis</text>
{''.join(vertical_grid)}{''.join(horizontal_grid)}{''.join(markers)}
<text x="120" y="112" class="section">RUN COUNT</text>{''.join(bars)}
<line x1="{plot_left}" y1="{baseline}" x2="{plot_right}" y2="{baseline}" stroke="#9aa0a6" stroke-width="1.5"/>
<text x="755" y="452" class="axisTitle">Lifecycle wall time (ms) · lower is faster →</text>
<rect x="120" y="470" width="1270" height="108" rx="14" fill="white" stroke="#dadce0"/>
<text x="137" y="491" class="section">RAW RUNS · EXACT LATENCY POSITION</text>
<line x1="120" y1="518" x2="1390" y2="518" class="hgrid"/><line x1="120" y1="550" x2="1390" y2="550" class="hgrid"/>{''.join(dots)}
<rect x="875" y="584" width="515" height="26" rx="13" class="callout"/><text x="1132" y="602" text-anchor="middle" class="guide">13 of 30 runs landed in the 420–430 ms interval</text>
<text x="120" y="603" class="foot">Excludes Cloud Run cold start, client RTT, Gemini latency, repository setup, and tests. Raw evidence: assets/evidence/latency.json.</text>
</svg></div></body></html>"""

OUT.write_text(html)
print(f"generated {OUT}")
