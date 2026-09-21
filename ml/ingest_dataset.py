"""Convert exported Migraine Detector datasets into the training input format.

Inputs:
  --readings   CSV from GET /api/dataset/export.csv (or any matching schema)
  --episodes   CSV from GET /api/reports/episodes.csv (optional; for labels)

The label `migraine_within_next_60m` = 1 for a reading that falls within 60
minutes of an episode start_time (if episodes provided), otherwise falls back
to the exported `risk_level == high`.

Output: ml/datasets/training.csv (columns expected by feature_engineering.py)
"""
from __future__ import annotations

import argparse
import os

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    raise SystemExit("ingest_dataset.py needs pandas (ml/requirements.txt)")

SIGNALS = ["heart_rate", "hrv", "systolic_bp", "diastolic_bp", "spo2", "temperature", "activity"]


def _episode_windows(episodes_csv: str) -> pd.DataFrame:
    df = pd.read_csv(episodes_csv)
    df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")
    df["end_time"] = pd.to_datetime(df["end_time"], errors="coerce")
    return df[["start_time", "end_time"]].dropna(subset=["start_time"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readings", required=True, help="readings CSV from /api/dataset/export.csv")
    parser.add_argument("--episodes", default=None, help="episodes CSV from /api/reports/episodes.csv")
    parser.add_argument("--user-id", type=int, default=1, help="id stamped on output rows")
    parser.add_argument("--window-minutes", type=int, default=60)
    parser.add_argument("--output", default=os.path.join(
        os.path.dirname(__file__), "datasets", "training.csv"))
    args = parser.parse_args()

    df = pd.read_csv(args.readings)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

    df["user_id"] = args.user_id
    for col in SIGNALS:
        df[col] = pd.to_numeric(df.get(col), errors="coerce")

    if args.episodes and os.path.exists(args.episodes):
        windows = _episode_windows(args.episodes)
        labels = []
        for ts in df["timestamp"]:
            labelled = 0
            for _, win in windows.iterrows():
                low = win["start_time"] - pd.Timedelta(minutes=args.window_minutes)
                high = win["end_time"] if pd.notna(win["end_time"]) else win["start_time"] + pd.Timedelta(hours=6)
                if low <= ts <= high:
                    labelled = 1
                    break
            labels.append(labelled)
        df["migraine_within_next_60m"] = labels
    elif "risk_level" in df.columns:
        df["migraine_within_next_60m"] = (df["risk_level"].astype(str).str.lower() == "high").astype(int)
        print("warning: no episodes provided; labelling from risk_level==high")
    else:
        raise SystemExit("Need --episodes or a risk_level column to build labels")

    keep = ["user_id", "timestamp"] + SIGNALS + ["migraine_within_next_60m"]
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    df[keep].to_csv(args.output, index=False)
    print(f"Wrote {os.path.abspath(args.output)} "
          f"({len(df)} rows, {int(df['migraine_within_next_60m'].sum())} positive)")


if __name__ == "__main__":
    main()