"""
SentinelAI operations dashboard — pairs with the FastAPI service.

Run: streamlit run dashboard/app.py
Env: SENTINEL_API_BASE (default http://127.0.0.1:8000/api/v1), SENTINEL_API_KEY (optional).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

API_BASE = os.environ.get("SENTINEL_API_BASE", "http://127.0.0.1:8000/api/v1").rstrip("/")


def _headers() -> dict[str, str]:
    key = os.environ.get("SENTINEL_API_KEY", "").strip()
    if key:
        return {"X-API-Key": key}
    return {}


@st.cache_data(ttl=5)
def fetch_health() -> dict | None:
    try:
        r = httpx.get(f"{API_BASE}/health", headers=_headers(), timeout=5.0)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None


@st.cache_data(ttl=5)
def fetch_transactions(limit: int, decision: str | None) -> list[dict]:
    params: dict[str, str | int] = {"limit": limit}
    if decision:
        params["decision"] = decision
    try:
        r = httpx.get(
            f"{API_BASE}/transactions",
            params=params,
            headers=_headers(),
            timeout=10.0,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        return []
    return []


@st.cache_data(ttl=10)
def fetch_metrics() -> dict | None:
    try:
        r = httpx.get(f"{API_BASE}/metrics", headers=_headers(), timeout=5.0)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None


def main() -> None:
    st.set_page_config(
        page_title="SentinelAI — Fraud Ops",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        """
        <style>
        .stApp { background: linear-gradient(165deg, #020617 0%, #0f172a 42%, #082f49 100%) !important; }
        .block-container { padding-top: 1.1rem; max-width: 1480px; }
        div[data-testid="stMetricValue"] { font-size: 1.65rem; font-weight: 700; letter-spacing: -0.02em; }
        div[data-testid="stMetricLabel"] { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.12em; }
        .hero-wrap {
            position: relative;
            overflow: hidden;
            border-radius: 16px;
            padding: 1.6rem 2rem 1.5rem 2rem;
            margin-bottom: 1.25rem;
            border: 1px solid rgba(148, 163, 184, 0.22);
            background: linear-gradient(125deg, rgba(15,23,42,0.95) 0%, rgba(8,47,73,0.55) 100%);
            box-shadow: 0 24px 48px -20px rgba(0,0,0,0.55);
        }
        .hero-wrap::before {
            content: "";
            position: absolute; inset: 0;
            background: radial-gradient(ellipse 70% 55% at 20% -10%, rgba(34,211,238,0.22), transparent 55%);
            pointer-events: none;
        }
        .hero-wrap h1 {
            position: relative;
            color: #f8fafc;
            margin: 0;
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: -0.03em;
        }
        .hero-wrap .tagline {
            position: relative;
            color: #94a3b8;
            margin: 0.55rem 0 0 0;
            font-size: 1.05rem;
            line-height: 1.45;
            max-width: 52rem;
        }
        .pill {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            font-size: 0.68rem;
            font-weight: 600;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            padding: 0.35rem 0.75rem;
            border-radius: 999px;
            border: 1px solid rgba(34,211,238,0.35);
            color: #a5f3fc;
            background: rgba(34,211,238,0.1);
            margin-bottom: 0.75rem;
        }
        .pill-dot { width: 7px; height: 7px; border-radius: 999px; background: #22d3ee; box-shadow: 0 0 12px #22d3ee; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    health = fetch_health()
    live = bool(health and health.get("model_loaded") and health.get("db_connected"))
    pill = (
        '<span class="pill"><span class="pill-dot"></span>Live API</span>'
        if live
        else '<span class="pill"><span class="pill-dot" style="background:#fbbf24;box-shadow:none"></span>Degraded</span>'
    )
    st.markdown(
        f'<div class="hero-wrap">{pill}<h1>SentinelAI — Fraud operations</h1>'
        "<p class='tagline'>Real-time scoring plane · SHAP drivers · rolling KPIs · "
        "PostgreSQL audit trail — portfolio surface for AI / ML engineering roles.</p></div>",
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.caption("API")
        st.code(API_BASE, language="text")
        st.divider()
        st.caption("Optional env: `SENTINEL_API_KEY` when the API uses API-key auth.")

    metrics = fetch_metrics()
    audit_preview = fetch_transactions(50, None)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        ok = health and health.get("model_loaded")
        st.metric("Model", "Loaded" if ok else "Offline", delta=None)
    with c2:
        db = health and health.get("db_connected")
        st.metric("Database", "Up" if db else "Down")
    with c3:
        served = (health or {}).get("total_predictions_served", 0)
        st.metric("Predictions served", f"{served:,}")
    with c4:
        lat = (metrics or {}).get("avg_processing_time_ms")
        st.metric("Avg latency (window)", f"{lat:.1f} ms" if lat is not None else "—")
    with c5:
        st.metric("Audit rows (loaded)", f"{len(audit_preview):,}")

    left, right = st.columns(2)

    with left:
        st.subheader("Decision mix (rolling window)")
        if metrics and metrics.get("total_predictions", 0) > 0:
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=["APPROVED", "REVIEW", "BLOCKED"],
                        y=[
                            metrics.get("approved_count", 0),
                            metrics.get("review_count", 0),
                            metrics.get("blocked_count", 0),
                        ],
                        marker_color=["#22c55e", "#eab308", "#ef4444"],
                    )
                ]
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#0f172a",
                font_color="#e2e8f0",
                height=320,
                margin=dict(l=20, r=20, t=30, b=40),
                yaxis_title="count",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No metrics yet — send traffic to `/api/v1/predict`.")

    with right:
        st.subheader("Fraud probability (recent)")
        rows = fetch_transactions(80, None)
        if rows:
            df = pd.DataFrame(rows)
            df["predicted_at"] = pd.to_datetime(df["predicted_at"])
            df = df.sort_values("predicted_at")
            fig2 = px.line(
                df,
                x="predicted_at",
                y="fraud_probability",
                color="decision",
                color_discrete_map={
                    "APPROVED": "#22c55e",
                    "REVIEW": "#eab308",
                    "BLOCKED": "#ef4444",
                },
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#0f172a",
                font_color="#e2e8f0",
                height=320,
                legend_title_text="",
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info(
                "No transactions in DB — start API + Postgres, then run "
                "`python scripts/seed_demo_traffic.py` before capturing screenshots."
            )

    st.subheader("Recent audit trail (latest scores)")
    audit = audit_preview
    if audit:
        adf = pd.DataFrame(audit)[
            [
                "transaction_id",
                "amount",
                "decision",
                "fraud_probability",
                "model_used",
                "predicted_at",
            ]
        ]
        st.dataframe(adf, use_container_width=True, hide_index=True)
    else:
        st.caption("No rows yet — seed demo traffic to populate this table for portfolio shots.")

    st.subheader("High-risk queue (BLOCKED / REVIEW)")
    flagged = fetch_transactions(25, "BLOCKED") + fetch_transactions(25, "REVIEW")
    flagged.sort(key=lambda x: x.get("predicted_at", ""), reverse=True)
    flagged = flagged[:40]
    if flagged:
        show = pd.DataFrame(flagged)[
            ["transaction_id", "amount", "decision", "fraud_probability", "predicted_at"]
        ]
        st.dataframe(show, use_container_width=True, hide_index=True)
    else:
        st.caption(
            "No BLOCKED/REVIEW rows yet — some models approve most demo vectors; "
            "the audit trail above still proves live scoring."
        )

    st.caption(
        f"Dashboard UTC {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} · "
        "SentinelAI portfolio / client demo surface."
    )


if __name__ == "__main__":
    main()
