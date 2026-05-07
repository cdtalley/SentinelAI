"""Feature definitions and engineering shared by training and serving."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

FEATURE_COLUMNS: list[str] = [
    "scaled_amount",
    "scaled_time",
    "V1",
    "V2",
    "V3",
    "V4",
    "V5",
    "V6",
    "V7",
    "V8",
    "V9",
    "V10",
    "V11",
    "V12",
    "V13",
    "V14",
    "V15",
    "V16",
    "V17",
    "V18",
    "V19",
    "V20",
    "V21",
    "V22",
    "V23",
    "V24",
    "V25",
    "V26",
    "V27",
    "V28",
    "hour_of_day",
    "is_night",
    "amount_log",
    "amount_bin_0",
    "amount_bin_1",
    "amount_bin_2",
    "amount_bin_3",
    "amount_bin_4",
]


def engineer_features(
    df: pd.DataFrame,
    scaler: StandardScaler | None = None,
    fit_scaler: bool = False,
) -> tuple[pd.DataFrame, StandardScaler]:
    """Build model features used at train and inference time."""
    required = ["Time", "Amount"] + [f"V{i}" for i in range(1, 29)]
    for c in required:
        if c not in df.columns:
            raise ValueError(f"Missing required column: {c}")

    out = df.copy()

    amt = out["Amount"].astype(float).values.reshape(-1, 1)
    tim = out["Time"].astype(float).values.reshape(-1, 1)
    stacked = np.hstack([amt, tim])

    if scaler is None:
        scaler = StandardScaler()
    if fit_scaler:
        scaler.fit(stacked)
    scaled = scaler.transform(stacked)
    out["scaled_amount"] = scaled[:, 0]
    out["scaled_time"] = scaled[:, 1]

    hour_float = (out["Time"] % 86400) / 3600.0
    out["hour_of_day"] = hour_float.astype(np.int64)
    hod = out["hour_of_day"]
    out["is_night"] = ((hod < 6) | (hod >= 22)).astype(np.int64)

    out["amount_log"] = np.log1p(out["Amount"].astype(float))

    bins = pd.cut(
        out["Amount"].astype(float),
        bins=[0, 10, 50, 200, 1000, np.inf],
        labels=False,
        include_lowest=True,
    )
    bins = bins.fillna(0).astype(int)
    bin_oh = pd.get_dummies(bins, prefix="amount_bin", dtype=int)
    for i in range(5):
        col = f"amount_bin_{i}"
        out[col] = bin_oh.get(col, np.zeros(len(out), dtype=int))

    feat_df = out[FEATURE_COLUMNS].copy()
    return feat_df.astype(float), scaler
