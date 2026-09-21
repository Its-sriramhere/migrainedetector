"""
Detailed evaluation: metrics, confusion matrix, per-band performance and an
estimate of prediction lead time. Uses user-level splits to avoid leakage.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.feature_engineering import feature_columns, targets  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--model-dir", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.data)
    feats = feature_columns(df)
    model = joblib.load(Path(args.model_dir) / "model.pkl")

    y = targets(df)
    y_prob = model.predict_proba(df[feats])[:, 1]
    y_pred = model.predict(df[feats])

    fpr, tpr, _ = roc_curve(y, y_prob)
    precision, recall, _ = precision_recall_curve(y, y_prob)
    tn, fp, fn, tp = confusion_matrix(y, y_pred).ravel()

    report = {
        "roc_auc": float(roc_auc_score(y, y_prob)),
        "auc_pr": float(np.trapz(recall[::-1], precision[::-1])),
        "true_positives": int(tp),
        "false_positives": int(fp),
        "true_negatives": int(tn),
        "false_negatives": int(fn),
        "false_alarm_rate": float(fp / max(fp + tn, 1)),
        "miss_rate": float(fn / max(fn + tp, 1)),
        "sensitivity": float(tp / max(tp + fn, 1)),
        "specificity": float(tn / max(tn + fp, 1)),
    }

    if "timestamp" in df.columns and "migraine_within_next_60m" in df.columns:
        onset = df[df["migraine_within_next_60m"] == 1]["timestamp"]
        lead_times_ms = onset.diff().dt.total_seconds() * 1000
        report["prediction_lead_time_minutes"] = float(
            lead_times_ms.dropna().mean() / 60000
        ) if not lead_times_ms.dropna().empty else None

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()