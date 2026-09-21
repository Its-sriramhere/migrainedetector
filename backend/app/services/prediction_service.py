from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..core.config import settings
from ..core.security import utcnow
from ..ml.heuristic_engine import HeuristicEngine
from ..models import Alert, AlertAdvice, Prediction, PredictionFeature, SensorReading, UserRiskProfile
from ..websocket.manager import manager
from . import baseline_service
from .advice import build_advice
from .baseline_service import baseline_for, risk_factors_from_profile
from .notifications import send_alert_notification

engine = HeuristicEngine()
ENGINE = engine

MODERATE_COOLDOWN_MINUTES = 60


def reload_engine() -> None:
    """Re-load thresholds after recalibration, used by the datasets API."""
    engine.reload()
    baseline_service._defaults_engine.reload()


def _window_predictions(db: Session, user_id: int) -> list[Prediction]:
    return (
        db.execute(
            select(Prediction)
            .where(Prediction.user_id == user_id)
            .order_by(Prediction.timestamp.desc())
            .limit(30)
        )
        .scalars()
        .all()
    )


def _weekly_seconds(db: Session, user_id: int) -> int:
    read_row = db.execute(
        select(func.min(SensorReading.timestamp)).where(SensorReading.user_id == user_id)
    ).scalar_one_or_none()
    if not read_row:
        return 0
    delta = utcnow() - read_row
    return max(0, int(delta.total_seconds()))


def create_prediction(
    db: Session,
    user_id: int,
    signal: dict,
    source: str = "pi",
    store_readings: bool = True,
    device_id: Optional[int] = None,
    engine: Optional[HeuristicEngine] = None,
) -> Prediction:
    engine = engine or ENGINE
    profile = db.execute(
        select(UserRiskProfile).where(UserRiskProfile.user_id == user_id)
    ).scalar_one_or_none()

    if store_readings:
        from ..models import SensorReading as SR

        reading = SR(
            user_id=user_id,
            device_id=device_id,
            source=source,
            heart_rate=signal.get("heart_rate"),
            hrv=signal.get("hrv"),
            systolic_bp=signal.get("systolic_bp"),
            diastolic_bp=signal.get("diastolic_bp"),
            spo2=signal.get("spo2"),
            temperature=signal.get("temperature"),
            activity=signal.get("activity"),
            signal_quality=signal.get("signal_quality"),
        )
        db.add(reading)

    baseline = baseline_for(db, user_id, profile)
    factors = risk_factors_from_profile(profile)
    result = engine.evaluate(signal, baseline, factors)

    prediction = Prediction(
        user_id=user_id,
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        prediction_window=settings.DEFAULT_PREDICTION_WINDOW_MINUTES,
        model_version=engine.model_version,
        source=source,
    )
    db.add(prediction)
    db.flush()

    for attr in result.contributions:
        db.add(
            PredictionFeature(
                prediction_id=prediction.id,
                feature_name=attr.feature_name,
                feature_value=attr.feature_value,
                contribution=attr.contribution,
            )
        )

    db.commit()
    db.refresh(prediction)

    alert = _maybe_alert(db, prediction, engine)
    if alert:
        send_alert_notification(db, user_id, alert.id, alert.risk_level, alert.message)
    elif prediction.risk_level in ("high", "moderate"):
        _log_cooldown_skip(db, prediction)
    db.commit()

    _publish(db, prediction)
    if alert:
        _publish_alert(db, alert)

    return prediction


def _publish(db: Session, prediction: Prediction) -> None:
    import asyncio

    features = db.execute(
        select(PredictionFeature).where(PredictionFeature.prediction_id == prediction.id)
    ).scalars().all()
    message = {
        "type": "prediction_update",
        "risk_score": prediction.risk_score,
        "risk_level": prediction.risk_level,
        "timestamp": prediction.timestamp.isoformat(),
        "prediction_window_minutes": prediction.prediction_window,
        "features": [
            {"feature_name": f.feature_name, "feature_value": f.feature_value,
             "contribution": f.contribution}
            for f in features
        ],
        "advice": [item["guidance"] for item in build_advice(prediction.risk_level, features)],
    }
    try:
        asyncio.get_running_loop().create_task(manager.broadcast_to_user(prediction.user_id, message))
    except RuntimeError:
        pass


def _publish_alert(db: Session, alert: Alert) -> None:
    import asyncio

    message = {
        "type": "alert_update",
        "id": alert.id,
        "risk_score": alert.risk_score,
        "risk_level": alert.risk_level,
        "message": alert.message,
        "timestamp": alert.timestamp.isoformat(),
        "acknowledged": alert.acknowledged,
        "prediction_id": alert.prediction_id,
        "advice": alert.advice_texts,
    }
    try:
        asyncio.get_running_loop().create_task(manager.broadcast_to_user(alert.user_id, message))
    except RuntimeError:
        pass


def _maybe_alert(db: Session, prediction: Prediction,
                 engine: Optional[HeuristicEngine] = None) -> Optional[Alert]:
    engine = engine or ENGINE
    if prediction.risk_level not in ("high", "moderate"):
        return None

    recent = db.execute(
        select(Alert)
        .where(
            Alert.user_id == prediction.user_id,
            Alert.risk_score >= engine.band_low,
        )
        .order_by(Alert.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    if recent and (utcnow() - recent.timestamp).total_seconds() < MODERATE_COOLDOWN_MINUTES * 60:
        return None

    if prediction.risk_level == "high":
        message = (
            "Elevated migraine risk detected. Your current physiological pattern "
            "differs from your personal baseline."
        )
    else:
        message = (
            "Your physiological pattern is starting to differ from your personal "
            "baseline. Consider resting and following your usual management plan."
        )

    advice = build_advice(prediction.risk_level, prediction.features)
    if advice:
        message += "\n\nReduce risk now:\n" + "\n".join(
            f"{item['step']}) {item['guidance']}" for item in advice
        )

    alert = Alert(
        user_id=prediction.user_id,
        prediction_id=prediction.id,
        risk_score=prediction.risk_score,
        risk_level=prediction.risk_level,
        message=message,
    )
    db.add(alert)
    db.flush()

    for item in advice:
        db.add(
            AlertAdvice(
                alert_id=alert.id,
                step=item["step"],
                guidance=item["guidance"],
            )
        )
    return alert


def _log_cooldown_skip(db: Session, prediction: Prediction) -> None:
    """Transparency row: risk is high/moderate but the alert was suppressed
    by the cooldown window. Deduped so a long risk stream doesn't flood the
    notification log — at most one row per user per cooldown window.
    """
    from ..models import NotificationLog

    recent = db.execute(
        select(NotificationLog)
        .where(
            NotificationLog.user_id == prediction.user_id,
            NotificationLog.status == "skipped",
            NotificationLog.alert_id.is_(None),
        )
        .order_by(NotificationLog.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if recent and (utcnow() - recent.created_at).total_seconds() < MODERATE_COOLDOWN_MINUTES * 60:
        return

    db.add(
        NotificationLog(
            user_id=prediction.user_id,
            alert_id=None,
            kind="sms",
            provider="cooldown",
            recipient=settings.ALERT_SMS_TO or "unset",
            risk_level=prediction.risk_level,
            status="skipped",
            detail=f"within {MODERATE_COOLDOWN_MINUTES}-minute alert cooldown — no duplicate alert created",
            message="",
        )
    )


def latest_prediction(db: Session, user_id: int) -> Optional[Prediction]:
    return (
        db.execute(
            select(Prediction)
            .where(Prediction.user_id == user_id)
            .order_by(Prediction.timestamp.desc())
            .limit(1)
        )
        .options(joinedload(Prediction.features))
        .scalars()
        .first()
    )


def get_predictions(db: Session, user_id: int, limit: int = 50) -> list[Prediction]:
    return (
        db.execute(
            select(Prediction)
            .where(Prediction.user_id == user_id)
            .order_by(Prediction.timestamp.desc())
            .limit(limit)
        )
        .options(joinedload(Prediction.features))
        .scalars()
        .all()
    )