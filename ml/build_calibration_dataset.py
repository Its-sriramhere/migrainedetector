"""Build the merged calibration CSV consumed by ``calibrate.py``.

Ingests the uploaded Migraine Detector datasets plus the synthetic patient-side
health-monitoring file (heart rate only) into a single frame with
per-signal label columns:

    timestamp, source, patient_id, heart_rate, systolic_bp, diastolic_bp,
    spo2, temperature, activity, episode, hr_abnormal

- ``episode`` marks migraine episodes from the 3 essential CSVs
  (BP / SpO2 / temperature).
- ``hr_abnormal`` marks abnormal heart-rate rows from the synthetic
  health-monitoring dataset (proxy label; the file is not migraine-labeled).

Heart rate is calibrated against its own proxy label so it does not pollute
the migraine-labeled signals.

Run:
    python build_calibration_dataset.py --input ml/datasets --output ml/datasets/calibration.csv
"""
from __future__ import annotations

import argparse
import os

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    raise SystemExit("build_calibration_dataset.py needs pandas (ml/requirements.txt)")

BP_FILE = "migraine_BP_50000.csv"
SPO2_FILE = "migraine_SpO2_50000.csv"
TEMP_FILE = "migraine_Temperature_50000.csv"
HR_FILE = "Synthetic_patient-HealthCare-Monitoring_dataset.csv"

OUT_COLUMNS = [
    "timestamp", "source", "patient_id", "heart_rate",
    "systolic_bp", "diastolic_bp", "spo2", "temperature", "activity",
    "episode", "hr_abnormal",
]


def _read_migraine(directory: str) -> pd.DataFrame:
    bp = pd.read_csv(os.path.join(directory, BP_FILE))
    spo2 = pd.read_csv(os.path.join(directory, SPO2_FILE))
    temp = pd.read_csv(os.path.join(directory, TEMP_FILE))

    merged = bp[["timestamp", "patient_id", "systolic_bp_mmHg", "diastolic_bp_mmHg", "migraine_label"]].rename(
        columns={
            "systolic_bp_mmHg": "systolic_bp",
            "diastolic_bp_mmHg": "diastolic_bp",
            "migraine_label": "episode",
        }
    )
    spo2_cols = spo2[["timestamp", "patient_id", "spo2_percent", "migraine_label"]].rename(
        columns={"spo2_percent": "spo2", "migraine_label": "episode"}
    )
    temp_cols = temp[["timestamp", "patient_id", "temperature_c", "migraine_label"]].rename(
        columns={"temperature_c": "temperature", "migraine_label": "episode"}
    )

    merged = merged.merge(spo2_cols, on=["timestamp", "patient_id"], how="outer", suffixes=("", "_s"))
    merged = merged.merge(temp_cols, on=["timestamp", "patient_id"], how="outer", suffixes=("", "_t"))
    merged["episode"] = merged["episode"].fillna(merged["episode_s"]).fillna(merged["episode_t"])
    merged = merged.drop(columns=["episode_s", "episode_t"])
    merged["source"] = "migraine_dataset"
    merged["heart_rate"] = None
    merged["hr_abnormal"] = None
    return merged


def _read_hr(directory: str) -> pd.DataFrame:
    df = pd.read_csv(os.path.join(directory, HR_FILE), encoding="latin-1")

    patients = df["Patient Number"].astype(str)
    rows = len(df)
    # The file has no timestamps; synthesize a 5-minute cadence so ordering holds.
    steps = pd.date_range("2026-01-01", periods=rows, freq="5min")
    if patients.duplicated().any():
        raise SystemExit(
            f"{HR_FILE}: expected one row per patient timestamp (got duplicate patients)."
        )

    hr = df[["Patient Number", "Heart Rate (bpm)", "Heart Rate Alert"]].copy()
    hr["timestamp"] = steps
    hr["source"] = "synthetic_healthcare"
    hr["patient_id"] = hr["Patient Number"]
    hr["heart_rate"] = pd.to_numeric(hr["Heart Rate (bpm)"], errors="coerce")
    hr["hr_abnormal"] = (hr["Heart Rate Alert"].astype(str).str.strip().str.upper() == "ABNORMAL").astype(int)
    hr["systolic_bp"] = None
    hr["diastolic_bp"] = None
    hr["spo2"] = None
    hr["temperature"] = None
    hr["activity"] = None
    hr["episode"] = None
    return hr[OUT_COLUMNS]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=os.path.dirname(os.path.abspath(__file__)) + "/datasets",
                        help="directory holding the raw CSV files")
    parser.add_argument("--output", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "datasets", "calibration.csv"))
    args = parser.parse_args()

    parts = [_read_migraine(args.input), _read_hr(args.input)]
    merged = pd.concat(parts, ignore_index=True)
    merged["timestamp"] = pd.to_datetime(merged["timestamp"], errors="coerce")
    merged = merged.sort_values("timestamp").reset_index(drop=True)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    merged.to_csv(args.output, index=False)

    print(f"Wrote {os.path.abspath(args.output)} ({len(merged)} rows)")
    print("migraine episode rows:", int(merged['episode'].fillna(0).astype(int).sum()))
    print("hr_abnormal rows:", int(merged['hr_abnormal'].fillna(0).astype(int).sum()))


if __name__ == "__main__":
    main()