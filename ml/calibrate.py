"""Derive HeuristicEngine thresholds from migraine datasets.

Run:
    python -m calibrate --data datasets/calibration.csv \
        --label-cols '{"heart_rate": "hr_abnormal"}' \
        --output ../backend/app/ml/thresholds.json

The merged CSV is produced by ``build_calibration_dataset.py``. It holds the
engine signal columns (``heart_rate``, ``systolic_bp``, ``diastolic_bp``,
``spo2``, ``temperature``, ``activity``) plus label columns. Each signal is
calibrated against its *own* label column when one is mapped (heart rate uses
the synthetic ``hr_abnormal`` proxy), otherwise the default ``episode`` label
(migraine rows) is used.

Writes ``thresholds.json`` consumed by ``HeuristicEngine``: band edges,
per-signal deviation triggers + weights, dataset baselines and ``demo_presets``
(normal / moderate / high signal vectors for the simulation). Falls back
gracefully to sensible defaults for the signals not present.
"""
from __future__ import annotations

import argparse
import json
import os

try:
    import numpy as np
    import pandas as pd
except ImportError:  # pragma: no cover
    raise SystemExit("calibrate.py needs pandas + numpy (ml/requirements.txt)")

SIGNALS = ["heart_rate", "hrv", "systolic_bp", "diastolic_bp", "spo2", "temperature", "activity"]

# Signals the engine expects with *pct-deviation-from-baseline* triggers.
PCT_TRIGGER_SIGNALS = {"heart_rate", "hrv", "systolic_bp", "diastolic_bp"}
# Signals whose engine trigger is an *absolute deviation*.
ABS_TRIGGER_SIGNALS = {"temperature", "spo2"}

REFERENCE_POINTS = {
    "heart_rate": 15.0,
    "hrv": 15.0,
    "systolic_bp": 12.0,
    "diastolic_bp": 10.0,
    "spo2": 5.0,
    "temperature": 8.0,
    "activity": 8.0,
}

DEFAULT_CONFIG: dict = {
    "band_edges": {"low": 30, "high": 70},
    "deviations": {
        "static_floor": 8.0,
        "hr_trigger_pct": 5.0,
        "hr_weight": 0.9,
        "hrv_trigger_pct": -5.0,
        "hrv_weight": 0.8,
        "bp_trigger_pct": 3.0,
        "bp_weight": 0.6,
        "spo2_drop": 1.0,
        "spo2_contribution": 5.0,
        "temp_dev": 0.6,
        "temp_weight": 3.0,
        "temp_cap": 6.0,
        "activity_dev_factor": 0.35,
        "activity_weight": 4.0,
        "activity_cap": 6.0,
        "sleep_weight": 0.8,
        "sleep_cap": 10.0,
        "stress_weight": 0.6,
        "stress_cap": 8.0,
        "trigger_weight": 0.9,
        "trigger_cap": 6.0,
    },
}

# Per-signal engine configuration keys.
SIGNAL_DEVIATION_KEYS = {
    "heart_rate": ("hr_trigger_pct", "hr_weight"),
    "hrv": ("hrv_trigger_pct", "hrv_weight"),
    "systolic_bp": ("bp_trigger_pct", "bp_weight"),
    "diastolic_bp": ("bp_trigger_pct", "bp_weight"),
    "spo2": ("spo2_drop", "spo2_contribution"),
    "temperature": ("temp_dev", "temp_weight"),
    "activity": ("activity_dev_factor", "activity_weight"),
}

SIGNAL_BASELINE_DEFAULTS = {
    "heart_rate": 72.0, "hrv": 48.0, "systolic_bp": 118.0, "diastolic_bp": 76.0,
    "spo2": 98.0, "temperature": 36.5, "activity": 0.5,
}


def _label_column(signal: str, label_col: str, extra_labels: dict[str, str]) -> str:
    return extra_labels.get(signal, label_col)


TRUE_LABELS = {"1", "1.0", "true", "yes", "high", "episode", "abnormal"}
FALSE_LABELS = {"0", "0.0", "false", "no", "normal", "clean"}


def _label_series(df: pd.DataFrame, label: str) -> pd.Series:
    return df[label].astype(str).str.strip().str.lower()


def _clean_episode(df: pd.DataFrame, signal: str, label: str):
    col = pd.to_numeric(df[signal], errors="coerce")
    lbl = _label_series(df, label)
    clean = df[lbl.isin(FALSE_LABELS)]
    episode = df[lbl.isin(TRUE_LABELS)]
    return col, clean, episode


def _pct_dev(ser: pd.Series, baseline: float) -> pd.Series:
    if baseline in (0, None):
        return pd.Series(dtype=float)
    return (ser - baseline) * 100.0 / baseline


def _median_p90(series: pd.Series):
    arr = pd.to_numeric(series, errors="coerce").dropna().to_numpy()
    if len(arr) < 5:
        return None, None
    return float(np.median(arr)), float(np.percentile(arr, 90))


def _clip(value: float | None, lo: float, hi: float, default: float) -> float:
    if value is None:
        return default
    return float(min(hi, max(lo, value)))


def calibrate(df: pd.DataFrame, label_col: str = "episode",
              extra_labels: dict[str, str] | None = None) -> dict:
    extra_labels = extra_labels or {}
    deviations: dict = dict(DEFAULT_CONFIG["deviations"])
    baselines: dict[str, float | None] = {}
    demo: dict[str, dict] = {}

    for signal in SIGNALS:
        if signal not in df.columns:
            baselines[signal] = None
            continue

        label = _label_column(signal, label_col, extra_labels)
        if label not in df.columns:
            baselines[signal] = None
            continue

        col, clean, episode = _clean_episode(df, signal, label)
        clean_vals = col.loc[clean.index]
        clean_vals = clean_vals.dropna()
        ep_vals = col.loc[episode.index].dropna()
        if len(clean_vals) < 20 or len(ep_vals) < 10:
            baselines[signal] = None
            continue

        baseline = float(clean_vals.mean())
        baselines[signal] = baseline

        if signal in PCT_TRIGGER_SIGNALS:
            dev = _pct_dev(ep_vals, baseline).dropna()
            if len(dev) < 5:
                continue
            median, p90 = float(np.median(dev.to_numpy())), float(np.percentile(dev.to_numpy(), 90))
            if abs(median) < 1e-6:
                continue
            margin = max(abs(p90 - median), 0.5)
            key, weight_key = SIGNAL_DEVIATION_KEYS[signal]

            sign = -1.0 if signal == "hrv" else 1.0
            if signal == "hrv":
                # Engine triggers on a *drop* (negative pct).
                trigger = -max(1.0, abs(median) * 0.6)
                deviations[weight_key] = round(min(4.0, REFERENCE_POINTS[signal] / margin), 2)
            else:
                trigger = max(1.0, abs(median) * 0.6) * sign
                deviations[weight_key] = round(min(3.0 if signal in ("systolic_bp", "diastolic_bp") else 4.0,
                                                   REFERENCE_POINTS[signal] / margin), 2)
            deviations[key] = round(trigger, 2)
            demo[str(signal)] = {
                "normal": round(float(clean_vals.median()), 2),
                "moderate": round(float(ep_vals.median()), 2),
                "high": round(float(np.percentile(ep_vals.to_numpy(), 90)), 2),
            }
        elif signal in ABS_TRIGGER_SIGNALS:
            ep_vec = {
                "normal": round(float(clean_vals.median()), 2),
                "moderate": round(float(ep_vals.median()), 2),
                "high": round(float(np.percentile(ep_vals.to_numpy(), 90)), 2),
            }
            if signal == "spo2":
                drop_series = (baseline - ep_vals).dropna()
                if len(drop_series) < 5:
                    continue
                median, p90 = float(np.median(drop_series.to_numpy())), float(np.percentile(drop_series.to_numpy(), 90))
                if median < 1e-6:
                    continue
                margin = max(abs(p90 - median), 0.5)
                deviations["spo2_drop"] = round(max(0.5, median * 0.6), 2)
                deviations["spo2_contribution"] = round(min(5.0, REFERENCE_POINTS["spo2"] / margin), 2)
            else:  # temperature
                dev = (ep_vals - baseline).abs().dropna()
                if len(dev) < 5:
                    continue
                median, p90 = float(np.median(dev.to_numpy())), float(np.percentile(dev.to_numpy(), 90))
                if median < 1e-6:
                    continue
                margin = max(abs(p90 - median), 0.5)
                deviations["temp_dev"] = round(max(0.2, median * 0.6), 2)
                deviations["temp_weight"] = round(min(4.0, REFERENCE_POINTS["temperature"] / margin), 2)
            demo[signal] = ep_vec

    # BP trigger is derived from the max of systolic/diastolic pct deviation.
    sbp_base, dbp_base = baselines.get("systolic_bp"), baselines.get("diastolic_bp")
    if sbp_base and dbp_base:
        sbp_ep = pd.to_numeric(df["systolic_bp"], errors="coerce")
        dbp_ep = pd.to_numeric(df["diastolic_bp"], errors="coerce")
        episode_mask = _label_series(df, _label_column("systolic_bp", label_col, extra_labels)).isin(TRUE_LABELS)
        sys_dev = _pct_dev(sbp_ep.loc[episode_mask], sbp_base).dropna()
        dia_dev = _pct_dev(dbp_ep.loc[episode_mask], dbp_base).dropna()
        combined = pd.concat([sys_dev, dia_dev], ignore_index=True)
        if len(combined) >= 5:
            median = float(np.median(combined.to_numpy()))
            p90 = float(np.percentile(combined.to_numpy(), 90))
            if abs(median) > 1e-6:
                deviations["bp_trigger_pct"] = round(max(1.0, abs(median) * 0.6), 2)
                margin = max(abs(p90 - median), 0.5)
                deviations["bp_weight"] = round(min(3.0, REFERENCE_POINTS["systolic_bp"] / margin), 2)

    presets = _build_demo_presets(demo)
    config = {
        "calibrated": True,
        "source_data": "migraine datasets + synthetic HR calibration",
        "baselines": {k: (round(float(v), 2) if v is not None else None) for k, v in baselines.items()},
        "band_edges": {"low": DEFAULT_CONFIG["band_edges"]["low"], "high": DEFAULT_CONFIG["band_edges"]["high"]},
        "deviations": deviations,
        "demo_presets": presets,
    }
    return config


def _build_demo_presets(demo: dict[str, dict]) -> dict[str, dict]:
    """Compose full signal vectors for the three simulation scenarios.

    Uses the per-signal calibrated vectors where available and sensible
    defaults for the signals the datasets do not cover (hrv, activity).
    """
    defaults = {k: v for k, v in SIGNAL_BASELINE_DEFAULTS.items()}
    hrv_defaults = {"normal": 48, "moderate": 40, "high": 30}
    activity_defaults = {"normal": 0.55, "moderate": 0.4, "high": 0.25}

    presets: dict[str, dict] = {}
    for scenario in ("normal", "moderate", "high"):
        vec: dict = {"hrv": hrv_defaults[scenario], "activity": activity_defaults[scenario]}
        for signal, default in defaults.items():
            if signal in ("hrv", "activity"):
                continue
            d = demo.get(signal)
            vec[signal] = d[scenario] if d else default
        if "diastolic_bp" in vec and "systolic_bp" in vec:
            sbp, dbp = vec.get("systolic_bp"), vec.get("diastolic_bp")
            if sbp and dbp and sbp < dbp:
                sbp, dbp = dbp, sbp  # guard ordering
                vec["systolic_bp"], vec["diastolic_bp"] = sbp, dbp
        for key in ("heart_rate", "systolic_bp", "diastolic_bp"):
            if key in vec:
                vec[key] = round(float(vec[key]))
        if "temperature" in vec:
            vec["temperature"] = round(float(vec["temperature"]), 1)
        if "spo2" in vec:
            vec["spo2"] = round(float(vec["spo2"]))
        if "activity" in vec:
            vec["activity"] = round(float(vec["activity"]), 2)
        presets[scenario] = vec
    return presets


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="merged CSV (build_calibration_dataset.py)")
    parser.add_argument("--label-col", default="episode", help="default label column marking migraine rows (0/1)")
    parser.add_argument("--label-cols", default="{}",
                        help='JSON mapping signal->label column, e.g. \'{"heart_rate": "hr_abnormal"}\'')
    parser.add_argument("--output", default=os.path.join(
        os.path.dirname(__file__), "..", "backend", "app", "ml", "thresholds.json"))
    parser.add_argument("--band-low", type=float, default=None)
    parser.add_argument("--band-high", type=float, default=None)
    args = parser.parse_args()

    try:
        extra_labels = json.loads(args.label_cols)
    except ValueError:
        raise SystemExit("--label-cols must be valid JSON")

    df = pd.read_csv(args.data)
    config = calibrate(df, args.label_col, extra_labels)
    if args.band_low is not None:
        config["band_edges"]["low"] = args.band_low
    if args.band_high is not None:
        config["band_edges"]["high"] = args.band_high

    out = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2)

    print(f"Wrote {out}")
    print("Baselines:", json.dumps(config["baselines"], indent=2))
    print("Deviations (calibrated):")
    for k in ("hr_trigger_pct", "hr_weight", "bp_trigger_pct", "bp_weight",
              "spo2_drop", "spo2_contribution", "temp_dev", "temp_weight"):
        print(f"  {k} = {config['deviations'][k]}")
    print("Demo presets:", json.dumps(config["demo_presets"], indent=2))


if __name__ == "__main__":
    main()