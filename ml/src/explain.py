"""
SHAP-based explanation of a trained model's prediction.

    python -m src.explain --model-dir ../models/xgboost \
        --heart-rate 92 --hrv 26 ... 

Writes the explanation JSON and prints feature contributions (feature_name,
feature_value, contribution) sorted by absolute contribution.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np

try:
    import shap
except ImportError:
    shap = None

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--data", required=True, help="Feature csv used as SHAP background")
    parser.add_argument("--heart-rate", type=float, default=92)
    parser.add_argument("--hrv", type=float, default=26)
    parser.add_argument("--systolic-bp", type=float, default=138)
    parser.add_argument("--diastolic-bp", type=float, default=88)
    parser.add_argument("--spo2", type=float, default=97)
    parser.add_argument("--temperature", type=float, default=36.9)
    parser.add_argument("--activity", type=float, default=0.15)
    args = parser.parse_args()

    if shap is None:
        print("SHAP not installed. Run: pip install shap")
        sys.exit(1)

    model_dir = Path(args.model_dir)
    model = joblib.load(model_dir / "model.pkl")
    feats = json.loads((model_dir / "feature_names.json").read_text())

    import pandas as pd

    background = pd.read_csv(args.data)[feats].iloc[:100]
    explainer = shap.TreeExplainer(model)

    row: dict[str, float] = {}
    base = {
        "heart_rate": args.heart_rate, "hrv": args.hrv, "systolic_bp": args.systolic_bp,
        "diastolic_bp": args.diastolic_bp, "spo2": args.spo2,
        "temperature": args.temperature, "activity": args.activity,
    }
    for name in feats:
        matched = None
        for col in ("heart_rate", "hrv", "systolic_bp", "diastolic_bp", "spo2", "temperature", "activity"):
            if name == col or name.endswith(f"_{col}"):
                matched = col
                break
        row[name] = base.get(matched, 0.0)

    sample = pd.DataFrame([row], columns=feats).fillna(0.0)
    shap_values = explainer.shap_values(sample)
    if isinstance(shap_values, list):
        shap_values = shap_values[1]

    values = shap_values[0]
    contributions = [
        {"feature_name": name, "feature_value": float(sample[name].iloc[0]),
         "contribution": float(value)}
        for name, value in zip(feats, values)
    ]
    contributions.sort(key=lambda c: abs(c["contribution"]), reverse=True)
    print(json.dumps(contributions[:12], indent=2))


if __name__ == "__main__":
    main()