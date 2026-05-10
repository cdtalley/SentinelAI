#!/usr/bin/env python3
"""Render docs/screenshots/upwork-thumbnail.png (1200×630) for Upwork / catalog cards.

Readable at small sizes: bold type, high contrast, stack callouts — no Streamlit chrome.
Requires: pip install playwright && python -m playwright install chromium
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs" / "screenshots" / "upwork-thumbnail.png"

HTML = """<!DOCTYPE html>
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
    .stats {
      display: flex; gap: 18px; margin-top: 36px;
    }
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
    .stack {
      display: flex; flex-wrap: wrap; gap: 10px;
    }
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


def main() -> int:
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        cwd=str(REPO),
        check=False,
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".html",
        delete=False,
        encoding="utf-8",
    ) as f:
        f.write(HTML)
        path = f.name
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1200, "height": 630})
            page.goto(Path(path).as_uri(), wait_until="load", timeout=60_000)
            page.wait_for_timeout(800)
            page.screenshot(path=str(OUT))
            browser.close()
    finally:
        Path(path).unlink(missing_ok=True)
    print(f"Wrote {OUT.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
