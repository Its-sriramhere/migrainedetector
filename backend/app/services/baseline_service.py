from statistics import median
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ml.heuristic_engine import Baseline, HeuristicEngine, RiskFactors
from ..models import SensorReading, UserRiskProfile

# Calibrated dataset baselines (from thresholds.json) seed the defaults for
# users with fewer than 5 live readings.
_defaults_engine = HeuristicEngine()

RESTING_HR_FROM_Q12 = {
    "Less than 60": 57,
    "60–70": 65,
    "70–80": 75,
    "80–90": 85,
    "More than 90": 95,
    "Don't know": 72,
}

STRESS_SCORES = {"Rarely": 0.0, "Occasionally": 2.5, "Frequently": 5.0, "Almost daily": 8.0}

SLEEP_IRREGULARITY = {
    "Very consistent": 0.0,
    "Mostly consistent": 1.5,
    "Sometimes irregular": 4.0,
    "Very irregular": 7.0,
}

SLEEP_HOURS = {
    "Less than 5": 4.5,
    "5–6": 5.5,
    "6–7": 6.5,
    "7–8": 7.5,
    "More than 8": 8.5,
}

HYDRATION_DEVIATION = {"Low": 1.0, "Moderate": 0.5, "Good": 0.0, "Very good": 0.0}

CAFFEINE_DEVIATION = {
    "None": 0.0,
    "1 serving/day": 0.0,
    "2-3 servings/day": 1.0,
    "More than 3 servings/day": 1.5,
}


def risk_factors_from_profile(profile: Optional[UserRiskProfile]) -> RiskFactors:
    f = RiskFactors()
    if profile is None:
        return f

    f.migraine_history_score = max(0.0, float(profile.migraine_history_score or 0.0))

    stress = profile.stress_profile or ""
    f.stress_score = STRESS_SCORES.get(stress, 0.0)

    sleep = profile.sleep_profile or ""
    f.sleep_irregularity = SLEEP_IRREGULARITY.get(sleep, 0.0)

    if profile.sleep_hours:
        f.sleep_deviation = max(0.0, abs(float(profile.sleep_hours) - 7.5) / 3.0)

    f.trigger_load = max(0.0, len(profile.trigger_profile or []) * 1.5)

    hydration = profile.hydration_profile or ""
    f.hydration_deviation = HYDRATION_DEVIATION.get(hydration, 0.0)

    caffeine = profile.caffeine_profile or ""
    f.caffeine_deviation = CAFFEINE_DEVIATION.get(caffeine, 0.0)
    return f


def _default_hr_from_profile(profile: Optional[UserRiskProfile]) -> float:
    if profile and profile.resting_hr:
        return float(profile.resting_hr)
    calibrated = _defaults_engine.baselines.get("heart_rate")
    return float(calibrated) if calibrated else 72.0


def _default_for(field: str, fallback: float) -> float:
    calibrated = _defaults_engine.baselines.get(field)
    return float(calibrated) if calibrated else fallback


def baseline_for(db: Session, user_id: int, profile: Optional[UserRiskProfile] = None) -> Baseline:
    profile = profile or db.execute(
        select(UserRiskProfile).where(UserRiskProfile.user_id == user_id)
    ).scalar_one_or_none()

    reading_rows = (
        db.execute(
            select(SensorReading)
            .where(SensorReading.user_id == user_id)
            .order_by(SensorReading.timestamp.desc())
            .limit(200)
        )
        .scalars()
        .all()
    )
    readings = list(reversed(reading_rows))

    def med(field: str, default: float) -> float:
        values = [getattr(r, field) for r in readings if getattr(r, field) is not None]
        return median(values) if len(values) >= 5 else default

    base_hr = med("heart_rate", _default_hr_from_profile(profile))
    base = Baseline(
        heart_rate=base_hr,
        hrv=med("hrv", _default_for("hrv", 48.0)),
        systolic_bp=med("systolic_bp", _default_for("systolic_bp", 118.0)),
        diastolic_bp=med("diastolic_bp", _default_for("diastolic_bp", 76.0)),
        spo2=med("spo2", _default_for("spo2", 98.0)),
        temperature=med("temperature", _default_for("temperature", 36.5)),
        activity=med("activity", _default_for("activity", 0.5)),
    )

    return base