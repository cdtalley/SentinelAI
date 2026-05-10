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
        .block-container { padding-top: 1.2rem; }
        div[data-testid="stMetricValue"] { font-size: 1.75rem; font-weight: 600; }
        .hero {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0c4a6e 100%);
            padding: 1.75rem 2rem;
            border-radius: 12px;
            margin-bottom: 1.25rem;
            border: 1px solid #334155;
        }
        .hero h1 { color: #f8fafc; margin: 0; font-size: 1.85rem; letter-spacing: -0.02em; }
        .hero p { color: #94a3b8; margin: 0.5rem 0 0 0; font-size: 1rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="hero"><h1>SentinelAI</h1>'
        "<p>Real-time fraud scoring · SHAP explainability · PSI drift · PostgreSQL audit trail</p></div>",
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.caption("API")
        st.code(API_BASE, language="text")
        st.divider()
        st.caption("Optional env: `SENTINEL_API_KEY` when the API uses API-key auth.")

    health = fetch_health()
    metrics = fetch_metrics()

    c1, c2, c3, c4 = st.columns(4)
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
    audit = fetch_transactions(50, None)
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
