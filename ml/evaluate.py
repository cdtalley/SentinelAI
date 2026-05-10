"""Offline evaluation of saved models. Run from repo root: ``python ml/evaluate.py``."""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from ml.feature_engineering import FEATURE_COLUMNS, engineer_features  # noqa: E402


def main() -> None:
    settings = get_settings()
    data_path = ROOT / "ml" / "data" / "creditcard.csv"
    if not data_path.is_file():
        print(f"Missing {data_path}")
        sys.exit(1)

    model_dir = Path(settings.MODEL_DIR)
    paths = {
        "xgb": model_dir / settings.XGBOOST_MODEL_FILE,
        "scaler": model_dir / settings.SCALER_FILE,
    }
    for p in paths.values():
        if not p.is_file():
            print(f"Missing model artifact: {p}")
            sys.exit(1)

    df = pd.read_csv(data_path)
    X_df, _ = engineer_features(df, fit_scaler=False, scaler=joblib.load(paths["scaler"]))
    y = df["Class"].astype(int)
    X = X_df[FEATURE_COLUMNS]

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    clf: xgb.XGBClassifier = joblib.load(paths["xgb"])
    proba = clf.predict_proba(X_te)[:, 1]
    pred = (proba >= 0.5).astype(int)

    print("--- Classification report ---")
    print(classification_report(y_te, pred, digits=4))
    print("AUC-ROC:", round(roc_auc_score(y_te, proba), 4))
    print("AUC-PR:", round(average_precision_score(y_te, proba), 4))
    print("Confusion matrix:\n", confusion_matrix(y_te, pred))

    imp = clf.feature_importances_
    top_idx = np.argsort(imp)[::-1][:10]
    names = list(FEATURE_COLUMNS)
    print("\n--- Top 10 XGBoost feature importances ---")
    for i in top_idx:
        print(f"  {names[i]}: {imp[i]:.5f}")

    explainer = shap.TreeExplainer(clf)
    shap_vals = explainer.shap_values(X_te.iloc[:500])
    if isinstance(shap_vals, list):
        shap_vals = shap_vals[1]
    mean_abs = np.abs(shap_vals).mean(axis=0)
    top_shap = np.argsort(mean_abs)[::-1][:10]
    print("\n--- Mean |SHAP| (top 10, sample n=500) ---")
    for i in top_shap:
        print(f"  {names[i]}: {mean_abs[i]:.5f}")

    out_dir = ROOT / "ml" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    print("\nEvaluation complete. Optional plots can be added to ml/evaluate.py as needed.")


if __name__ == "__main__":
    main()
