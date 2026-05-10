#!/usr/bin/env python3
"""One-shot portfolio capture: wait for API, seed live traffic, run Streamlit, PNG screenshots.

Produces hiring-grade assets under docs/screenshots/:
  - upwork-dashboard.png      — Streamlit ops surface (full page, 1920-wide)
  - next-console-dashboard.png — Next.js /dashboard (if dev server responds)

Prerequisites: Python deps from requirements.txt (httpx, playwright) and
``python -m playwright install chromium`` once.

Examples::

    docker compose up -d --build
    python scripts/capture_portfolio_assets.py

    python scripts/capture_portfolio_assets.py --with-docker --wait-ready 600

    # Next.js capture only (Streamlit already captured):
    python scripts/capture_portfolio_assets.py --only next --skip-seed --next-url http://127.0.0.1:3010/dashboard
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[1]


def _port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def wait_api_ready(api_base: str, timeout: int, headers: dict[str, str]) -> None:
    """Wait until health reports DB + model (same gate as readiness for demos)."""
    url = f"{api_base.rstrip('/')}/health"
    deadline = time.time() + timeout
    last = ""
    while time.time() < deadline:
        try:
            r = httpx.get(url, headers=headers, timeout=5.0)
            if r.status_code == 200:
                body = r.json()
                if body.get("model_loaded") and body.get("db_connected"):
                    print(f"API ready: model_loaded={body.get('model_loaded')} db={body.get('db_connected')}")
                    return
                last = f"model_loaded={body.get('model_loaded')} db_connected={body.get('db_connected')}"
        except httpx.RequestError as e:
            last = str(e)
        time.sleep(2.0)
    raise SystemExit(f"API not ready within {timeout}s (last: {last})")


def wait_tcp(host: str, port: int, timeout: int) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _port_open(host, port):
            return
        time.sleep(0.5)
    raise SystemExit(f"TCP {host}:{port} not open within {timeout}s")


def ensure_playwright_browser() -> None:
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        cwd=str(REPO),
        check=False,
    )


def run_seed(api_base: str, env: dict[str, str]) -> int:
    seed = REPO / "scripts" / "seed_demo_traffic.py"
    r = subprocess.run(
        [sys.executable, str(seed), "--base", api_base.rstrip("/"), "--count", "36"],
        cwd=str(REPO),
        env=env,
    )
    return int(r.returncode)


def screenshot_url(url: str, out: Path, viewport: tuple[int, int], wait_ms: int) -> None:
    from playwright.sync_api import sync_playwright

    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": viewport[0], "height": viewport[1]})
        page.goto(url, wait_until="domcontentloaded", timeout=180_000)
        if "8501" in url or "streamlit" in url.lower():
            try:
                page.wait_for_selector('[data-testid="stApp"]', timeout=120_000)
            except Exception:
                pass
        else:
            try:
                page.get_by_text("Operations console", exact=False).first.wait_for(timeout=90_000)
            except Exception:
                pass
        page.wait_for_timeout(wait_ms)
        page.screenshot(path=str(out), full_page=True)
        browser.close()
    print(f"Wrote {out.resolve()}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--api-base",
        default="http://127.0.0.1:8000/api/v1",
        help="FastAPI v1 prefix",
    )
    parser.add_argument(
        "--wait-ready",
        type=int,
        default=420,
        help="Seconds to wait for /health model+db (default 420)",
    )
    parser.add_argument(
        "--with-docker",
        action="store_true",
        help="Run `docker compose up -d postgres api` from repo root first",
    )
    parser.add_argument("--skip-seed", action="store_true")
    parser.add_argument(
        "--only",
        choices=("all", "streamlit", "next"),
        default="all",
    )
    parser.add_argument(
        "--streamlit-url",
        default="http://127.0.0.1:8501",
    )
    parser.add_argument(
        "--next-url",
        default="http://127.0.0.1:3010/dashboard",
        help="Try this first; falls back to port 3000 if unreachable",
    )
    parser.add_argument(
        "--streamlit-wait-ms",
        type=int,
        default=20_000,
        help="Extra settle time after Streamlit load for Plotly + tables",
    )
    parser.add_argument(
        "--next-wait-ms",
        type=int,
        default=12_000,
    )
    args = parser.parse_args()

    api_base = args.api_base.rstrip("/")
    env = os.environ.copy()
    env["SENTINEL_API_BASE"] = api_base
    headers: dict[str, str] = {}
    key = os.environ.get("SENTINEL_API_KEY", "").strip()
    if key:
        headers["X-API-Key"] = key

    if args.with_docker:
        print("Starting docker compose (postgres + api)…")
        subprocess.run(
            ["docker", "compose", "up", "-d", "postgres", "api"],
            cwd=str(REPO),
            check=True,
        )

    if args.only in ("all", "streamlit"):
        wait_api_ready(api_base, args.wait_ready, headers)

    if args.only in ("all", "streamlit") and not args.skip_seed:
        print("Seeding demo predictions…")
        rc = run_seed(api_base, env)
        if rc != 0:
            print("Warning: seed script returned non-zero; continuing.", file=sys.stderr)
        time.sleep(6)

    ensure_playwright_browser()

    if args.only in ("all", "streamlit"):
        cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "dashboard/app.py",
            "--server.port",
            "8501",
            "--server.address",
            "127.0.0.1",
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ]
        creation = 0
        if sys.platform == "win32":
            creation = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        print("Starting Streamlit on :8501…")
        proc = subprocess.Popen(
            cmd,
            cwd=str(REPO),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            creationflags=creation,
        )
        try:
            wait_tcp("127.0.0.1", 8501, 120)
            time.sleep(3)
            out = REPO / "docs" / "screenshots" / "upwork-dashboard.png"
            screenshot_url(
                args.streamlit_url,
                out,
                (1920, 1080),
                args.streamlit_wait_ms,
            )
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proc.kill()

    if args.only in ("all", "next"):
        next_candidates = [args.next_url]
        if ":3010" in args.next_url:
            next_candidates.append(args.next_url.replace(":3010", ":3000"))
        for nu in next_candidates:
            try:
                r = httpx.get(nu, timeout=3.0)
                if r.status_code < 500:
                    out = REPO / "docs" / "screenshots" / "next-console-dashboard.png"
                    screenshot_url(nu, out, (1920, 1080), args.next_wait_ms)
                    break
            except httpx.RequestError:
                continue
        else:
            print("Next.js dashboard not reachable — skip next-console-dashboard.png", file=sys.stderr)

    print("\nPortfolio assets updated under docs/screenshots/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
