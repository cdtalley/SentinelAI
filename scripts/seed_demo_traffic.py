#!/usr/bin/env python3
"""POST diverse /api/v1/predict rows so ops UIs and screenshots show real traffic.

Requires a running API with models + DB (e.g. ``docker compose up``). Safe to
re-run: each row uses a fresh ``transaction_id``.

Usage:
  python scripts/seed_demo_traffic.py
  SENTINEL_API_BASE=http://127.0.0.1:8000/api/v1 SENTINEL_API_KEY=... python scripts/seed_demo_traffic.py
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import uuid
from typing import Any

import httpx


def _minimal_v() -> dict[str, float]:
    return {f"v{i}": 0.0 for i in range(1, 29)}


def _body(
    amount: float,
    t: float,
    overrides: dict[str, Any] | None = None,
    tx_id: str | None = None,
) -> dict[str, Any]:
    b: dict[str, Any] = {
        "transaction_id": tx_id or str(uuid.uuid4()),
        "amount": amount,
        "time": t,
        **_minimal_v(),
    }
    if overrides:
        b.update(overrides)
    return b


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        default=os.environ.get("SENTINEL_API_BASE", "http://127.0.0.1:8000/api/v1").rstrip(
            "/"
        ),
        help="API v1 prefix (default env SENTINEL_API_BASE or localhost)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=24,
        help="Number of synthetic scores to send (default 24)",
    )
    args = parser.parse_args()

    key = os.environ.get("SENTINEL_API_KEY", "").strip()
    headers: dict[str, str] = {}
    if key:
        headers["X-API-Key"] = key

    # Scenarios tuned to spread decisions across cold-start, typical, and stressed vectors.
    templates: list[tuple[float, float, dict[str, Any]]] = [
        (4.5, 120.0, {}),  # cold-start-ish
        (8.2, 200.0, {}),
        (45.0, 1500.0, {"v1": 0.5, "v2": -0.3}),
        (120.0, 8000.0, {"v3": -4.0, "v4": 5.0, "v5": 1.2}),
        (249.0, 12000.0, {"v1": 2.0, "v10": -3.0, "v11": 4.0}),
        (1200.0, 50000.0, {"v2": 8.0, "v3": -6.0, "v12": 2.5}),
        (85.0, 9000.0, {"v4": -2.0, "v7": 9.0}),
        (310.0, 22000.0, {"v5": 3.0, "v8": -2.0, "v14": 6.0}),
        (19.99, 400.0, {"v6": 1.5}),
        (999.0, 70000.0, {"v9": -5.0, "v10": 7.0, "v15": -4.0}),
        (72.5, 6500.0, {"v11": -1.0, "v16": 3.0}),
        (450.0, 40000.0, {"v12": 4.0, "v17": -8.0}),
        (33.0, 900.0, {}),
        (180.0, 18000.0, {"v1": -1.0, "v18": 5.0}),
        (890.0, 90000.0, {"v3": 6.0, "v19": -3.0, "v20": 2.0}),
        (150.0, 30000.0, {"v21": 1.0, "v22": -1.0}),
        (275.0, 45000.0, {"v23": 4.0, "v24": -2.0}),
        (60.0, 2500.0, {"v25": 0.5}),
        (520.0, 60000.0, {"v26": -4.0, "v27": 3.0, "v28": 1.0}),
    ]

    url = f"{args.base}/predict"
    ok = 0
    fail = 0
    with httpx.Client(timeout=120.0) as client:
        for i in range(max(1, args.count)):
            amt, t, extra = templates[i % len(templates)]
            t = t + float(i) * 37.0  # de-correlate time feature a bit
            body = _body(amt, t, extra)
            try:
                r = client.post(url, json=body, headers=headers)
                if r.status_code == 200:
                    ok += 1
                    dec = r.json().get("decision", "?")
                    p = r.json().get("fraud_probability", 0)
                    print(f"  OK {dec} p={float(p):.3f} amt={amt}")
                elif r.status_code == 409:
                    print("  skip duplicate (unexpected uuid clash)")
                else:
                    fail += 1
                    print(f"  FAIL {r.status_code} {r.text[:200]}")
            except httpx.RequestError as e:
                fail += 1
                print(f"  ERROR {e}", file=sys.stderr)
            time.sleep(0.05)

    print(f"\nDone: {ok} scored, {fail} failures. Open Streamlit dashboard or capture screenshot.")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
