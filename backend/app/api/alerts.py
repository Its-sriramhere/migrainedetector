from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..api.deps import get_current_user
from ..core.config import settings
from ..db.session import get_db
from ..models import Alert, NotificationLog, Prediction, User
from ..schemas import AlertFeedbackIn, AlertOut

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("/notifications")
def list_notifications(limit: int = 25, db: Session = Depends(get_db),
                       current: User = Depends(get_current_user)):
    """SMS delivery log for the alerts page (status: sent/skipped/failed/quota_exceeded)."""
    logs = (
        db.execute(
            select(NotificationLog)
            .where(NotificationLog.user_id == current.id)
            .order_by(NotificationLog.created_at.desc())
            .limit(min(limit, 200))
        )
        .scalars()
        .all()
    )
    return {
        "sms_enabled": settings.SMS_ENABLED,
        "sms_provider": settings.SMS_PROVIDER,
        "sms_max_sends": settings.SMS_MAX_SENDS,
        "logs": [
            {
                "id": log.id,
                "risk_level": log.risk_level,
                "provider": log.provider,
                "status": log.status,
                "detail": log.detail,
                "recipient": log.recipient,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
    }


@router.get("", response_model=list[AlertOut])
def list_alerts(limit: int = 50, db: Session = Depends(get_db),
                current: User = Depends(get_current_user)):
    return (
        db.execute(
            select(Alert)
            .where(Alert.user_id == current.id)
            .order_by(Alert.timestamp.desc())
            .limit(min(limit, 200))
        )
        .scalars()
        .all()
    )


@router.post("/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge(alert_id: int, db: Session = Depends(get_db),
                current: User = Depends(get_current_user)):
    alert = db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.user_id == current.id)
    ).scalar_one_or_none()
    if alert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    alert.acknowledged = True
    db.commit()
    db.refresh(alert)
    return alert


@router.post("/{alert_id}/feedback", response_model=AlertOut)
def feedback(alert_id: int, body: AlertFeedbackIn, db: Session = Depends(get_db),
             current: User = Depends(get_current_user)):
    alert = db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.user_id == current.id)
    ).scalar_one_or_none()
    if alert is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Alert not found")
    alert.feedback = body.feedback
    alert.acknowledged = True
    db.commit()

    if body.feedback == "yes" and alert.prediction_id:
        prediction = db.get(Prediction, alert.prediction_id)
        if prediction:
            prediction.outcome = "hit"
            db.commit()
    return alert