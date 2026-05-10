"""Capture a full-page PNG of the Streamlit dashboard (Playwright).

Prerequisites: API + DB + models up, then optionally seed traffic, Streamlit on 8501:

  python scripts/seed_demo_traffic.py
  streamlit run dashboard/app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true
  python scripts/capture_dashboard_screenshot.py --wait-ms 15000
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8501")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("docs/screenshots/upwork-dashboard.png"),
    )
    parser.add_argument(
        "--wait-ms",
        type=int,
        default=15_000,
        help="Wait after load for Streamlit charts + cache refresh (default 15000)",
    )
    parser.add_argument(
        "--seed-first",
        action="store_true",
        help="Run scripts/seed_demo_traffic.py before capture (needs live API)",
    )
    parser.add_argument(
        "--api-base",
        default="http://127.0.0.1:8000/api/v1",
        help="Passed to seed script as SENTINEL_API_BASE when --seed-first",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    seed = repo_root / "scripts" / "seed_demo_traffic.py"
    if args.seed_first:
        env = {**os.environ, "SENTINEL_API_BASE": args.api_base.rstrip("/")}
        r = subprocess.run(
            [sys.executable, str(seed), "--base", args.api_base.rstrip("/")],
            cwd=str(repo_root),
            env=env,
            check=False,
        )
        if r.returncode != 0:
            print(
                "seed_demo_traffic exited non-zero; capture may still show empty charts.",
                file=sys.stderr,
            )
        else:
            # Let Streamlit cache_data TTL expire so the UI refetches metrics + transactions.
            time.sleep(6)

    args.out.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 900})
        page.goto(args.url, wait_until="domcontentloaded", timeout=120_000)
        try:
            page.wait_for_selector('[data-testid="stApp"]', timeout=60_000)
        except Exception:
            pass
        page.wait_for_timeout(args.wait_ms)
        page.screenshot(path=str(args.out), full_page=True)
        browser.close()

    print(f"Wrote {args.out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
