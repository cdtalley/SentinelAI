#!/usr/bin/env python3
"""Render Upwork / catalog thumbnails (1200×630).

Writes:
  docs/screenshots/upwork-thumbnail.png   — v2 (high-impact, click-optimized)
  docs/screenshots/upwork-thumbnail-v1.png — classic layout (original design, reproducible)

Requires: pip install playwright && python -m playwright install chromium
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_V1 = REPO / "docs" / "screenshots" / "upwork-thumbnail-v1.png"
OUT_V2 = REPO / "docs" / "screenshots" / "upwork-thumbnail.png"

# Classic v1 (first version you liked) — kept in code so it is always reproducible.
THUMB_V1_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700;800&family=JetBrains+Mono:wght@500;600&display=swap" rel="stylesheet"/>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      width: 1200px; height: 630px; margin: 0;
      font-family: Inter, system-ui, sans-serif;
      background: radial-gradient(120% 90% at 10% 0%, rgba(34,211,238,0.18), transparent 50%),
                  linear-gradient(155deg, #020617 0%, #0f172a 38%, #0c4a6e 100%);
      color: #f1f5f9;
      overflow: hidden;
      position: relative;
    }
    .grid {
      position: absolute; inset: 0;
      background-image: linear-gradient(rgba(148,163,184,0.06) 1px, transparent 1px),
                          linear-gradient(90deg, rgba(148,163,184,0.06) 1px, transparent 1px);
      background-size: 48px 48px;
      mask-image: linear-gradient(to bottom, black 40%, transparent);
      pointer-events: none;
    }
    .wrap { position: relative; z-index: 1; padding: 48px 56px; height: 100%; display: flex; flex-direction: column; justify-content: space-between; }
    .eyebrow {
      font-family: "JetBrains Mono", monospace;
      font-size: 11px; font-weight: 600; letter-spacing: 0.22em; text-transform: uppercase;
      color: #22d3ee; margin-bottom: 14px;
    }
    h1 {
      font-size: 56px; font-weight: 800; letter-spacing: -0.04em; line-height: 1.05;
      max-width: 900px;
      background: linear-gradient(105deg, #fff 0%, #e2e8f0 45%, #67e8f9 100%);
      -webkit-background-clip: text; background-clip: text; color: transparent;
    }
    .sub {
      margin-top: 18px; font-size: 22px; color: #94a3b8; font-weight: 500; max-width: 820px; line-height: 1.45;
    }
    .stats { display: flex; gap: 18px; margin-top: 36px; }
    .stat {
      flex: 1; max-width: 200px;
      padding: 18px 20px;
      border-radius: 14px;
      border: 1px solid rgba(148,163,184,0.2);
      background: rgba(15,23,42,0.65);
      backdrop-filter: blur(8px);
    }
    .stat .v { font-family: "JetBrains Mono", monospace; font-size: 26px; font-weight: 700; color: #fff; }
    .stat .l { font-size: 11px; text-transform: uppercase; letter-spacing: 0.14em; color: #64748b; margin-top: 6px; }
    .stack { display: flex; flex-wrap: wrap; gap: 10px; }
    .chip {
      font-family: "JetBrains Mono", monospace;
      font-size: 12px; font-weight: 600;
      padding: 8px 14px; border-radius: 999px;
      border: 1px solid rgba(34,211,238,0.35);
      color: #a5f3fc; background: rgba(34,211,238,0.1);
    }
    .accent-bar {
      position: absolute; bottom: 0; left: 0; right: 0; height: 4px;
      background: linear-gradient(90deg, #22d3ee, #34d399, #a78bfa);
    }
  </style>
</head>
<body>
  <div class="grid"></div>
  <div class="wrap">
    <div>
      <div class="eyebrow">AI / ML engineering portfolio</div>
      <h1>SentinelAI — Fraud intelligence stack</h1>
      <p class="sub">FastAPI scoring · XGBoost + isolation forest · SHAP · Postgres audit · WebSocket alerts · Next.js console</p>
      <div class="stats">
        <div class="stat"><div class="v">4.6ms</div><div class="l">Avg latency</div></div>
        <div class="stat"><div class="v">2.8k</div><div class="l">Rolling window</div></div>
        <div class="stat"><div class="v">PSI</div><div class="l">Drift governance</div></div>
        <div class="stat"><div class="v">Live</div><div class="l">Ops dashboard</div></div>
      </div>
    </div>
    <div>
      <div class="stack">
        <span class="chip">FastAPI</span>
        <span class="chip">PostgreSQL</span>
        <span class="chip">XGBoost</span>
        <span class="chip">WebSockets</span>
        <span class="chip">Next.js 14</span>
        <span class="chip">Docker</span>
      </div>
    </div>
  </div>
  <div class="accent-bar"></div>
</body>
</html>
"""

# v2: asymmetric layout, faux product chrome, outcome headline for scroll-stopping at small size.
THUMB_V2_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=JetBrains+Mono:wght@500;600&display=swap" rel="stylesheet"/>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      width: 1200px; height: 630px; margin: 0;
      font-family: Syne, Inter, system-ui, sans-serif;
      background: #020617;
      color: #f8fafc;
      overflow: hidden;
      position: relative;
    }
    .glow {
      position: absolute; width: 720px; height: 720px; right: -180px; top: -240px;
      background: radial-gradient(circle, rgba(34,211,238,0.35) 0%, transparent 68%);
      pointer-events: none;
    }
    .glow2 {
      position: absolute; width: 520px; height: 520px; left: -120px; bottom: -200px;
      background: radial-gradient(circle, rgba(167,139,250,0.22) 0%, transparent 70%);
      pointer-events: none;
    }
    .noise {
      position: absolute; inset: 0; opacity: 0.04;
      background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
      pointer-events: none;
    }
    .row { position: relative; z-index: 2; display: flex; height: 100%; }
    .left {
      flex: 1.05;
      padding: 44px 48px 44px 52px;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }
    .kicker {
      font-family: "JetBrains Mono", monospace;
      font-size: 12px; font-weight: 600;
      letter-spacing: 0.28em; text-transform: uppercase;
      color: #22d3ee;
      margin-bottom: 16px;
    }
    .brand { font-size: 26px; font-weight: 800; letter-spacing: -0.03em; color: #fff; margin-bottom: 8px; }
    .hook {
      font-size: 62px; font-weight: 800; line-height: 0.98;
      letter-spacing: -0.045em;
      max-width: 640px;
      text-shadow: 0 2px 40px rgba(0,0,0,0.45);
    }
    .hook span { color: #22d3ee; }
    .proof {
      margin-top: 22px;
      font-family: "JetBrains Mono", monospace;
      font-size: 15px; color: #94a3b8; line-height: 1.55; max-width: 560px;
    }
    .proof strong { color: #e2e8f0; font-weight: 600; }
    .cta-row {
      margin-top: 28px;
      display: flex; gap: 12px; flex-wrap: wrap;
    }
    .pill {
      font-family: "JetBrains Mono", monospace;
      font-size: 11px; font-weight: 600;
      letter-spacing: 0.06em;
      padding: 9px 16px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,0.14);
      background: rgba(255,255,255,0.06);
      color: #cbd5e1;
    }
    .pill-hot {
      border-color: rgba(34,211,238,0.55);
      background: rgba(34,211,238,0.12);
      color: #ecfeff;
    }
    .right {
      width: 460px;
      padding: 36px 44px 36px 0;
      display: flex; align-items: center; justify-content: flex-end;
    }
    .window {
      width: 100%; max-width: 420px;
      border-radius: 14px;
      border: 1px solid rgba(148,163,184,0.25);
      background: linear-gradient(165deg, rgba(15,23,42,0.95), rgba(2,6,23,0.92));
      box-shadow: 0 32px 80px -20px rgba(0,0,0,0.75), 0 0 0 1px rgba(34,211,238,0.12);
      overflow: hidden;
    }
    .titlebar {
      display: flex; align-items: center; gap: 8px;
      padding: 12px 14px;
      border-bottom: 1px solid rgba(255,255,255,0.06);
      background: rgba(0,0,0,0.25);
    }
    .dot { width: 10px; height: 10px; border-radius: 50%; }
    .tb-label { margin-left: 8px; font-family: "JetBrains Mono", monospace; font-size: 11px; color: #64748b; letter-spacing: 0.04em; }
    .win-body { padding: 18px 16px 22px; }
    .bars { display: flex; align-items: flex-end; gap: 8px; height: 120px; margin-top: 8px; }
    .b {
      flex: 1; border-radius: 6px 6px 2px 2px;
      background: linear-gradient(180deg, #22d3ee, #0891b2);
      opacity: 0.9;
    }
    .b:nth-child(2) { height: 72%; }
    .b:nth-child(3) { height: 100%; }
    .b:nth-child(4) { height: 48%; }
    .b:nth-child(5) { height: 88%; }
    .b:nth-child(6) { height: 58%; }
    .b:nth-child(7) { height: 92%; }
    .row-metrics { display: flex; gap: 10px; margin-top: 16px; }
    .m {
      flex: 1; padding: 10px 10px;
      border-radius: 10px;
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.06);
    }
    .m .n { font-family: "JetBrains Mono", monospace; font-size: 20px; font-weight: 700; color: #fff; }
    .m .t { font-size: 9px; text-transform: uppercase; letter-spacing: 0.12em; color: #64748b; margin-top: 4px; }
    .badges { display: flex; gap: 6px; margin-top: 14px; flex-wrap: wrap; }
    .bd { font-size: 10px; font-weight: 700; padding: 5px 9px; border-radius: 6px; font-family: "JetBrains Mono", monospace; }
    .bd-g { background: rgba(34,197,94,0.2); color: #86efac; }
    .bd-y { background: rgba(234,179,8,0.2); color: #fde047; }
    .bd-r { background: rgba(244,63,94,0.2); color: #fda4af; }
    .strip {
      position: absolute; bottom: 0; left: 0; right: 0; height: 6px;
      background: linear-gradient(90deg, #22d3ee, #34d399, #a78bfa, #f472b6);
    }
    .ribbon {
      position: absolute; top: 22px; right: -48px;
      transform: rotate(38deg);
      background: linear-gradient(90deg, #f43f5e, #fb7185);
      color: white; font-family: "JetBrains Mono", monospace;
      font-size: 11px; font-weight: 700; letter-spacing: 0.18em;
      padding: 8px 72px;
      box-shadow: 0 8px 24px rgba(244,63,94,0.35);
    }
  </style>
</head>
<body>
  <div class="glow"></div>
  <div class="glow2"></div>
  <div class="noise"></div>
  <div class="ribbon">PORTFOLIO PIECE</div>
  <div class="row">
    <div class="left">
      <div class="kicker">Hire-ready · full stack</div>
      <div class="brand">SentinelAI</div>
      <div class="hook">Fraud scores<br/><span>in milliseconds</span></div>
      <p class="proof">
        <strong>FastAPI</strong> inference · <strong>XGBoost + IF</strong> ensemble path ·
        <strong>SHAP</strong> narratives · <strong>Postgres</strong> audit ·
        <strong>WebSocket</strong> alerts · <strong>Next.js</strong> ops console
      </p>
      <div class="cta-row">
        <span class="pill pill-hot">ML + API + UI</span>
        <span class="pill">Docker · CI · Alembic</span>
        <span class="pill">PSI drift · KPIs</span>
      </div>
    </div>
    <div class="right">
      <div class="window">
        <div class="titlebar">
          <span class="dot" style="background:#fb7185"></span>
          <span class="dot" style="background:#fbbf24"></span>
          <span class="dot" style="background:#4ade80"></span>
          <span class="tb-label">sentinelai · ops</span>
        </div>
        <div class="win-body">
          <div class="bars">
            <div class="b" style="height:55%"></div>
            <div class="b"></div>
            <div class="b"></div>
            <div class="b"></div>
            <div class="b"></div>
            <div class="b"></div>
            <div class="b"></div>
          </div>
          <div class="row-metrics">
            <div class="m"><div class="n">4.6ms</div><div class="t">p50 latency</div></div>
            <div class="m"><div class="n">2.8k</div><div class="t">window</div></div>
            <div class="m"><div class="n">SHAP</div><div class="t">explain</div></div>
          </div>
          <div class="badges">
            <span class="bd bd-g">APPROVED</span>
            <span class="bd bd-y">REVIEW</span>
            <span class="bd bd-r">BLOCKED</span>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="strip"></div>
</body>
</html>
"""


def _render(html: str, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".html",
        delete=False,
        encoding="utf-8",
    ) as f:
        f.write(html)
        path = f.name
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": 1200, "height": 630},
                device_scale_factor=2,
            )
            page.goto(Path(path).as_uri(), wait_until="load", timeout=90_000)
            page.wait_for_timeout(1200)
            page.screenshot(path=str(out))
            browser.close()
    finally:
        Path(path).unlink(missing_ok=True)


def main() -> int:
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        cwd=str(REPO),
        check=False,
    )
    _render(THUMB_V1_HTML, OUT_V1)
    _render(THUMB_V2_HTML, OUT_V2)
    print(f"v1 (classic): {OUT_V1.resolve()}")
    print(f"v2 (default): {OUT_V2.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
