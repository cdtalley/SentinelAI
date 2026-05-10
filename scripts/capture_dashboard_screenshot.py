"""Capture a full-page PNG of the Streamlit dashboard (Playwright).

Prerequisites: ``streamlit run dashboard/app.py`` on port 8501, then:
  python scripts/capture_dashboard_screenshot.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8501")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("docs/screenshots/upwork-dashboard.png"),
    )
    parser.add_argument("--wait-ms", type=int, default=8000)
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 900})
        page.goto(args.url, wait_until="domcontentloaded", timeout=120_000)
        page.wait_for_timeout(args.wait_ms)
        page.screenshot(path=str(args.out), full_page=True)
        browser.close()

    print(f"Wrote {args.out.resolve()}")


if __name__ == "__main__":
    main()
