"""
Model training entry point.

Trains Logistic Regression, Random Forest and XGBoost classifiers on the
extracted feature frame and writes model artifacts to ml/models.

Example:
    python -m src.train --data ../data/processed/features.csv --output ../models
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, roc_auc_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from xgboost import XGBClassifier
except ImportError:
    XGBClassifier = None

from .feature_engineering import feature_columns, targets
from .preprocessing import train_valid_test_split_by_user


def make_models() -> dict[str, Any]:
    models = {
        "logistic_regression": Pipeline(
            [("scaler", StandardScaler()), ("clf", LogisticRegression(max_iter=2000))]
        ),
        "random_forest": RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1),
    }
    if XGBClassifier is not None:
        models["xgboost"] = XGBClassifier(
            n_estimators=200, max_depth=4, learning_rate=0.05,
            eval_metric="logloss", random_state=42,
        )
    return models


def evaluate(model: Any, X: pd.DataFrame, y_true: pd.Series) -> dict[str, float]:
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1]
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_true, y_prob),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Path to feature csv")
    parser.add_argument("--output", default=str(Path(__file__).resolve().parents[1] / "models"))
    args = parser.parse_args()

    df = pd.read_csv(args.data)
    feats = feature_columns(df)
    y = targets(df)

    X_train, X_valid, X_test = train_valid_test_split_by_user(df)
    y_train, y_valid, y_test = targets(X_train), targets(X_valid), targets(X_test)

    summary: dict[str, dict[str, float]] = {}
    best_name, best_f1 = None, -1.0
    for name, model in make_models().items():
        model.fit(X_train[feats], y_train)
        scores = evaluate(model, X_test[feats], y_test)
        summary[name] = scores
        if scores["f1"] > best_f1:
            best_name, best_f1 = name, scores["f1"]

        out_dir = Path(args.output) / name
        out_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, out_dir / "model.pkl")
        (out_dir / "feature_names.json").write_text(json.dumps(feats, indent=2))

    metadata = {
        "best_model": best_name,
        "best_test_f1": best_f1,
        "n_train": len(X_train), "n_valid": len(X_valid), "n_test": len(X_test),
        "results": summary,
    }
    Path(args.output).mkdir(parents=True, exist_ok=True)
    (Path(args.output) / "training_summary.json").write_text(json.dumps(metadata, indent=2))
    print("Best:", best_name, "F1:", round(best_f1, 3))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()