"""
Prediction interface for a trained model artifact.

    python -m src.predict --model-dir ../models/xgboost --heart-rate 92 --hrv 26 ...
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--heart-rate", type=float, default=None)
    parser.add_argument("--hrv", type=float, default=None)
    parser.add_argument("--systolic-bp", type=float, default=None)
    parser.add_argument("--diastolic-bp", type=float, default=None)
    parser.add_argument("--spo2", type=float, default=None)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--activity", type=float, default=None)
    args = parser.parse_args()

    model_dir = Path(args.model_dir)
    model = joblib.load(model_dir / "model.pkl")
    feats = json.loads((model_dir / "feature_names.json").read_text())

    base = {
        "heart_rate": 72, "hrv": 48, "systolic_bp": 118, "diastolic_bp": 76,
        "spo2": 98, "temperature": 36.5, "activity": 0.5,
    }
    values = {
        "heart_rate": args.heart_rate, "hrv": args.hrv, "systolic_bp": args.systolic_bp,
        "diastolic_bp": args.diastolic_bp, "spo2": args.spo2,
        "temperature": args.temperature, "activity": args.activity,
    }
    for k, v in values.items():
        if v is None:
            values[k] = base[k]

    row: np.ndarray = np.zeros(len(feats))
    for i, name in enumerate(feats):
        matched = None
        for col in ("heart_rate", "hrv", "systolic_bp", "diastolic_bp", "spo2", "temperature", "activity"):
            if name == col or name.endswith(f"_{col}"):
                matched = col
                break
        row[i] = values.get(matched, 0.0)

    prob = float(model.predict_proba(row.reshape(1, -1))[:, 1].item())
    level = "high" if prob > 0.70 else "moderate" if prob >= 0.30 else "low"
    print(json.dumps({
        "risk_score": round(prob * 100, 1),
        "risk_level": level,
        "prediction_window_minutes": 60,
    }, indent=2))


if __name__ == "__main__":
    main()