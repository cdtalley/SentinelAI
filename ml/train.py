"""Offline training — run from repository root: ``python ml/train.py``."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings
from ml.feature_engineering import FEATURE_COLUMNS, engineer_features


def main() -> None:
    settings = get_settings()
    data_path = ROOT / "ml" / "data" / "creditcard.csv"
    if not data_path.is_file():
        print(
            "Dataset not found. Download from:\n"
            "https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud\n"
            f"Save as: {data_path}"
        )
        sys.exit(1)

    df = pd.read_csv(data_path)
    print(f"shape={df.shape} fraud_count={int(df['Class'].sum())} fraud_rate={df['Class'].mean():.4%}")

    X_df, scaler = engineer_features(df, fit_scaler=True)
    y = df["Class"].astype(int)
    X = X_df[FEATURE_COLUMNS]

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    for fold, (tr_idx, va_idx) in enumerate(skf.split(X, y), 1):
        clf = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.05,
            scale_pos_weight=float((y.iloc[tr_idx] == 0).sum() / max(1, (y.iloc[tr_idx] == 1).sum())),
            eval_metric="auc",
            random_state=42,
            n_jobs=-1,
        )
        clf.fit(X.iloc[tr_idx], y.iloc[tr_idx])
        proba = clf.predict_proba(X.iloc[va_idx])[:, 1]
        print(
            f"fold {fold} AUC-ROC={roc_auc_score(y.iloc[va_idx], proba):.4f} "
            f"AUC-PR={average_precision_score(y.iloc[va_idx], proba):.4f}"
        )

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    pos_w = float((y_tr == 0).sum() / max(1, (y_tr == 1).sum()))
    xgb_model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        scale_pos_weight=pos_w,
        eval_metric="aucpr",
        random_state=42,
        n_jobs=-1,
    )
    xgb_model.fit(X_tr, y_tr)
    p_test = xgb_model.predict_proba(X_te)[:, 1]
    auc_roc = float(roc_auc_score(y_te, p_test))
    auc_pr = float(average_precision_score(y_te, p_test))
    print(f"holdout AUC-ROC={auc_roc:.4f} AUC-PR={auc_pr:.4f}")
    print(classification_report(y_te, (p_test >= 0.5).astype(int), digits=4))
    print("confusion_matrix\n", confusion_matrix(y_te, (p_test >= 0.5).astype(int)))

    X_nf = X[y == 0]
    iso = IsolationForest(
        n_estimators=200,
        contamination=0.002,
        random_state=42,
        n_jobs=-1,
    )
    iso.fit(X_nf)

    out_dir = Path(settings.MODEL_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(xgb_model, out_dir / settings.XGBOOST_MODEL_FILE)
    joblib.dump(iso, out_dir / settings.ISOLATION_FOREST_FILE)
    joblib.dump(scaler, out_dir / settings.SCALER_FILE)
    with open(out_dir / settings.FEATURE_NAMES_FILE, "w", encoding="utf-8") as f:
        json.dump(FEATURE_COLUMNS, f)

    meta_path = out_dir / "model_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "version": settings.MODEL_VERSION,
                "auc_roc": auc_roc,
                "auc_pr": auc_pr,
                "n_train_samples": int(len(X_tr)),
                "fraud_rate": float(y.mean()),
                "feature_count": len(FEATURE_COLUMNS),
            },
            f,
            indent=2,
        )
    print("Training complete. Models saved to", out_dir.resolve())


if __name__ == "__main__":
    main()
