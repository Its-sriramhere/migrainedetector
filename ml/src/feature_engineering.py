"""
Time-window feature engineering.

Each input row becomes a row of aggregated features computed over a configured
look-back window plus deviation-from-personal-baseline features used to
personalize predictions.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

WINDOW_COLUMNS = [
    "heart_rate",
    "hrv",
    "systolic_bp",
    "diastolic_bp",
    "spo2",
    "temperature",
    "activity",
]


def build_feature_frame(
    df: pd.DataFrame, window: int = 10, label_col: str = "migraine_within_next_60m"
) -> pd.DataFrame:
    """Sliding-window feature extraction plus lags and baseline deviations."""
    records: list[dict] = []
    for _, user_df in df.groupby("user_id"):
        user_df = user_df.reset_index(drop=True)
        n = len(user_df)
        for i in range(n):
            lo = max(0, i - window + 1)
            w = user_df.iloc[lo:i + 1]
            record: dict = {
                "user_id": user_df.loc[i, "user_id"],
                "timestamp": user_df.loc[i, "timestamp"],
            }
            for col in WINDOW_COLUMNS:
                series = pd.to_numeric(w[col], errors="coerce").astype(float)
                record[f"{col}_mean"] = series.mean()
                record[f"{col}_std"] = series.std()
                record[f"{col}_min"] = series.min()
                record[f"{col}_max"] = series.max()
                if len(series) > 1:
                    record[f"{col}_slope"] = np.polyfit(np.arange(len(series)), series, 1)[0]
                else:
                    record[f"{col}_slope"] = 0.0
                record[f"{col}_change"] = series.iloc[-1] - series.iloc[0]
                if f"{col}_dev" in user_df.columns:
                    record[f"{col}_baseline_dev"] = user_df.loc[i, f"{col}_dev"]
            if label_col in user_df.columns:
                record[label_col] = int(user_df.loc[i, label_col])
            records.append(record)

    features = pd.DataFrame(records)
    return features


FEATURE_PREFIXES = WINDOW_COLUMNS
NON_FEATURE_COLUMNS = {"user_id", "timestamp", "migraine_within_next_60m"}


def feature_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in NON_FEATURE_COLUMNS and c.endswith(("_mean", "_std", "_min", "_max", "_slope", "_change", "_baseline_dev"))]


def targets(df: pd.DataFrame) -> pd.Series:
    return df["migraine_within_next_60m"].astype(int)