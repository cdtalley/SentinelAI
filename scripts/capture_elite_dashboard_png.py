#!/usr/bin/env python3
"""Write docs/screenshots/upwork-dashboard.png using portfolio preview (no API required).

Runs Streamlit with an unreachable API base so the dashboard renders **synthetic**
elite telemetry (clearly labeled in-UI). Use ``capture_portfolio_assets.py`` when
you want a **live** screenshot with real scored rows.

Usage::
    pip install playwright && python -m playwright install chromium
    python scripts/capture_elite_dashboard_png.py
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _port_open(host: str, port: int) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def main() -> int:
    env = os.environ.copy()
    env["SENTINEL_API_BASE"] = "http://127.0.0.1:1/api/v1"
    env["SENTINEL_PORTFOLIO_PREVIEW"] = "1"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "dashboard/app.py",
        "--server.port",
        "8512",
        "--server.address",
        "127.0.0.1",
        "--server.headless",
        "true",
    ]
    creation = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
    proc = subprocess.Popen(
        cmd,
        cwd=str(REPO),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        creationflags=creation,
    )
    try:
        for _ in range(120):
            if _port_open("127.0.0.1", 8512):
                break
            time.sleep(0.5)
        else:
            raise SystemExit("Streamlit did not open port 8512 in time")

        time.sleep(4)
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            cwd=str(REPO),
            check=False,
        )
        out = REPO / "docs" / "screenshots" / "upwork-dashboard.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            page.goto("http://127.0.0.1:8512", wait_until="domcontentloaded", timeout=120_000)
            try:
                page.wait_for_selector('[data-testid="stApp"]', timeout=90_000)
            except Exception:
                pass
            page.wait_for_timeout(22_000)
            page.screenshot(path=str(out), full_page=True)
            browser.close()
        print(f"Wrote {out.resolve()}")
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=12)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
