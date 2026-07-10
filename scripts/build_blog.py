#!/usr/bin/env python3
# ruff: noqa: E501
"""Build a self-contained reviewable blog directory from docs/tutorial.md."""

from __future__ import annotations

import shutil
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "tutorial.md"
OUT = ROOT / "site"
ASSETS = [
    ROOT / "assets" / "architecture.png",
    ROOT / "assets" / "full-review-results.png",
    ROOT / "assets" / "adk-agent-design.png",
    ROOT / "assets" / "adk-test-plan.png",
    ROOT / "assets" / "deep-dive-differentiation.png",
    ROOT / "assets" / "latency-results.png",
    ROOT / "assets" / "cost-breakdown.png",
    ROOT / "assets" / "platform-decision-matrix.png",
    ROOT / "assets" / "annotated-tool-sequence.png",
    ROOT / "assets" / "annotated-security-probe.png",
    ROOT / "assets" / "annotated-failing-tests.png",
    ROOT / "assets" / "screenshots" / "adk-web-full-flow.png",
    ROOT / "assets" / "evidence" / "full-review.json",
    ROOT / "assets" / "evidence" / "latency.json",
]


def flatten_local_links(text: str) -> str:
    for asset in ASSETS:
        patterns = [
            f"../assets/{asset.name}",
            f"../assets/screenshots/{asset.name}",
            f"../assets/evidence/{asset.name}",
        ]
        for pattern in patterns:
            text = text.replace(pattern, asset.name)
    text = text.replace(
        "decision-matrix.md",
        "https://github.com/thomas-chong/cloud-run-sandbox-adk-deep-dive/blob/main/docs/decision-matrix.md",
    )
    return text


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    text = flatten_local_links(SOURCE.read_text())
    md = markdown.Markdown(
        extensions=["fenced_code", "tables", "toc", "sane_lists"],
        extension_configs={"toc": {"permalink": True, "toc_depth": "2-3"}},
    )
    article = md.convert(text)
    toc = md.toc
    html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="A measured deep dive into Gemini 3.5 Flash, Google ADK, and native Cloud Run sandboxes.">
<title>The agent that runs the PR is part of the threat model</title>
<style>
@font-face {{ font-family:'Google Sans Flex Variable'; font-style:normal; font-display:swap; font-weight:1 1000; src:url(https://cdn.jsdelivr.net/fontsource/fonts/google-sans-flex:vf@latest/latin-wght-normal.woff2) format('woff2-variations'); }}
:root {{ --ink:#202124; --muted:#5f6368; --line:#dadce0; --blue:#1967d2; --blue2:#4285f4; --green:#188038; --red:#d93025; --yellow:#f9ab00; --paper:#fff; --wash:#f8fafd; --code:#202124; }}
* {{ box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{ margin:0; font-family:'Google Sans Flex Variable','Google Sans',Arial,sans-serif; color:var(--ink); background:var(--paper); font-size:18px; line-height:1.68; }}
a {{ color:var(--blue); text-decoration-thickness:1px; text-underline-offset:3px; }}
.topbar {{ position:sticky; top:0; z-index:20; height:64px; display:flex; align-items:center; justify-content:space-between; padding:0 32px; border-bottom:1px solid var(--line); background:rgba(255,255,255,.94); backdrop-filter:blur(14px); }}
.brand {{ font-weight:720; letter-spacing:-.3px; }}
.topbar nav {{ display:flex; gap:22px; font-size:15px; font-weight:650; }}
.hero {{ background:radial-gradient(circle at 90% 10%,#d2e3fc 0,transparent 28%),linear-gradient(135deg,#f8fafd,#fff 55%); border-bottom:1px solid var(--line); padding:72px max(24px,calc((100vw - 1160px)/2)); }}
.eyebrow {{ color:var(--blue); font-size:14px; font-weight:760; letter-spacing:1.3px; text-transform:uppercase; }}
.hero h1 {{ max-width:1000px; font-size:clamp(46px,6vw,78px); line-height:1.02; letter-spacing:-2.6px; margin:18px 0 20px; }}
.hero p {{ max-width:840px; color:var(--muted); font-size:22px; }}
.badges {{ display:flex; flex-wrap:wrap; gap:10px; margin-top:28px; }}
.badge {{ border:1px solid #a8c7fa; background:#e8f0fe; color:#174ea6; border-radius:999px; padding:7px 12px; font-size:14px; font-weight:650; }}
.layout {{ width:min(1440px,calc(100% - 40px)); margin:0 auto; display:grid; grid-template-columns:260px minmax(0,900px); gap:64px; align-items:start; }}
.toc {{ position:sticky; top:88px; max-height:calc(100vh - 110px); overflow:auto; margin-top:54px; padding:20px 18px; border:1px solid var(--line); border-radius:18px; background:var(--wash); font-size:14px; line-height:1.4; }}
.toc > ul {{ padding-left:18px; margin:0; }} .toc ul {{ list-style:none; padding-left:12px; }} .toc li {{ margin:8px 0; }} .toc a {{ color:var(--muted); text-decoration:none; }}
article {{ min-width:0; padding:56px 0 120px; }}
article > h1 {{ display:none; }}
h2 {{ font-size:40px; line-height:1.15; letter-spacing:-1.1px; margin:84px 0 22px; scroll-margin-top:90px; }}
h3 {{ font-size:27px; line-height:1.25; margin:52px 0 14px; scroll-margin-top:90px; }}
p,li {{ color:#303134; }}
blockquote {{ margin:28px 0; padding:20px 24px; background:#e8f0fe; border-left:5px solid var(--blue2); border-radius:0 14px 14px 0; }}
blockquote p {{ margin:0; }}
img {{ width:100%; height:auto; display:block; margin:34px 0 12px; border:1px solid var(--line); border-radius:18px; box-shadow:0 12px 36px rgba(60,64,67,.10); }}
pre {{ overflow:auto; padding:22px 24px; border-radius:16px; background:var(--code); color:#e8eaed; font:500 14px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace; }}
code {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.88em; background:#f1f3f4; border-radius:5px; padding:.1em .35em; }}
pre code {{ background:none; padding:0; color:inherit; }}
table {{ width:100%; border-collapse:separate; border-spacing:0; margin:28px 0; font-size:15px; display:block; overflow-x:auto; }}
th {{ background:#f1f3f4; font-weight:720; text-align:left; }} th,td {{ padding:13px 15px; border-right:1px solid var(--line); border-bottom:1px solid var(--line); vertical-align:top; }} th:first-child,td:first-child {{ border-left:1px solid var(--line); }} tr:first-child th {{ border-top:1px solid var(--line); }}
hr {{ border:0; border-top:1px solid var(--line); margin:72px 0; }}
.headerlink {{ opacity:0; margin-left:8px; text-decoration:none; }} h2:hover .headerlink,h3:hover .headerlink {{ opacity:.5; }}
.raw-note {{ background:#202124; color:#fff; border-radius:18px; padding:22px 26px; margin:32px 0; }}
footer {{ border-top:1px solid var(--line); padding:34px; text-align:center; color:var(--muted); font-size:14px; }}
@media (max-width:1050px) {{ .layout {{ grid-template-columns:1fr; width:min(900px,calc(100% - 32px)); }} .toc {{ display:none; }} article {{ padding-top:24px; }} }}
@media (max-width:640px) {{ body {{ font-size:16px; }} .topbar nav {{ display:none; }} .hero {{ padding:48px 22px; }} .hero h1 {{ letter-spacing:-1.5px; }} h2 {{ font-size:32px; }} article {{ padding-bottom:70px; }} }}
</style>
</head>
<body>
<header class="topbar"><div class="brand">Cloud Run Sandbox × ADK</div><nav><a href="#the-measured-result-first">Evidence</a><a href="#cost-optimization-tokens-dominate-this-example">Cost</a><a href="#cloud-run-versus-gke-and-hosted-sandbox-services">Compare</a><a href="https://github.com/thomas-chong/cloud-run-sandbox-adk-deep-dive">GitHub</a></nav></header>
<section class="hero"><div class="eyebrow">Developer deep dive · verified July 9, 2026</div><h1>The agent that runs the PR is part of the threat model</h1><p>A measured implementation of Gemini 3.5 Flash, Google ADK, and native Cloud Run sandboxes—complete with raw events, boundary probes, latency distributions, and cost math.</p><div class="badges"><span class="badge">19.10 s full repair turn</span><span class="badge">428.347 ms lifecycle p50</span><span class="badge">30/30 benchmark runs</span><span class="badge">14 local tests</span></div></section>
<div class="layout"><aside class="toc">{toc}</aside><article>{article}</article></div>
<footer>Measured evidence, not a synthetic benchmark. Cloud Run sandboxes remain Public Preview.</footer>
</body></html>'''
    (OUT / "index.html").write_text(html)
    for asset in ASSETS:
        if not asset.exists():
            raise FileNotFoundError(asset)
        shutil.copy2(asset, OUT / asset.name)
    print(f"Built {OUT / 'index.html'} with {len(ASSETS)} assets")


if __name__ == "__main__":
    build()
