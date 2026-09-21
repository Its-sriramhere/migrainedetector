"""
Data preprocessing helpers for the migraine early-warning dataset.

Expected CSV / dataframe columns (one row per timestamped measurement window):

    user_id, timestamp, heart_rate, hrv, systolic_bp, diastolic_bp,
    spo2, temperature, activity, sleep_hours, migraine_within_next_60m (0/1)

Missing keys should be handled before feature extraction. Rows are grouped by
user so that the personal baseline can be computed and so that user-level
train/valid/test splits avoid data leakage.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

BASELINE_COLUMNS = [
    "heart_rate",
    "hrv",
    "systolic_bp",
    "diastolic_bp",
    "spo2",
    "temperature",
    "activity",
]


def load_csv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"user_id", "timestamp"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["user_id", "timestamp"]).reset_index(drop=True)
    return df


def add_personal_baseline(df: pd.DataFrame, min_obs: int = 5) -> pd.DataFrame:
    """Adds personal-baseline columns computed from the user's own history."""
    out = df.copy()
    for col in BASELINE_COLUMNS:
        base = (
            out.groupby("user_id")[col]
            .rolling(min_obs, min_periods=min_obs)
            .median()
            .reset_index(level=0, drop=True)
            .shift(1)
        ) if col in out else pd.Series(index=out.index, dtype=float)
        out[f"{col}_baseline"] = base
        out[f"{col}_dev"] = out[col] - out[f"{col}_baseline"]
    return out


def handle_missing(df: pd.DataFrame, threshold: float = 0.85) -> pd.DataFrame:
    keep = [c for c in df.columns if df[c].isna().mean() < (1 - threshold)]
    return df[keep]


def train_valid_test_split_by_user(
    df: pd.DataFrame, valid_users: int = 2, test_users: int = 2, seed: int = 42
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Leakage-safe split: whole users are assigned to one fold."""
    rng = np.random.default_rng(seed)
    user_ids = df["user_id"].unique()
    rng.shuffle(user_ids)
    test_ids = set(user_ids[:test_users])
    valid_ids = set(user_ids[test_users:test_users + valid_users])
    train = df[~df["user_id"].isin(valid_ids | test_ids)]
    valid = df[df["user_id"].isin(valid_ids)]
    test = df[df["user_id"].isin(test_ids)]
    return train, valid, test