"""Signal-quality validation for physiological readings."""

PLAUSIBLE = {
    "heart_rate": (35.0, 200.0),
    "hrv": (10.0, 180.0),
    "systolic_bp": (70.0, 220.0),
    "diastolic_bp": (40.0, 140.0),
    "spo2": (85.0, 100.0),
    "temperature": (34.0, 41.0),
    "activity": (0.0, 1.0),
}


def check_signal(sample: dict) -> dict:
    """Sets signal_quality to 0 (untrusted) when a value is implausible."""
    ok = True
    for field, (lo, hi) in PLAUSIBLE.items():
        value = sample.get(field)
        if value is None:
            continue
        if not (lo <= value <= hi):
            ok = False
            break
    sample["signal_quality"] = 0.9 if ok else 0.0
    return sample


def is_trusted(sample: dict, min_quality: float = 0.5) -> bool:
    return (sample.get("signal_quality") or 0.0) >= min_quality