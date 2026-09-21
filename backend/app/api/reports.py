from typing import Optional

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..api.deps import get_current_user
from ..core.security import utcnow
from ..db.session import get_db
from ..models import Alert, MigraineEpisode, Prediction, SensorReading, User
from ..schemas import ReportOverview

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/overview", response_model=ReportOverview)
def overview(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    uid = current.id

    total_readings = db.execute(
        select(func.count(SensorReading.id)).where(SensorReading.user_id == uid)
    ).scalar_one()
    total_predictions = db.execute(
        select(func.count(Prediction.id)).where(Prediction.user_id == uid)
    ).scalar_one()
    total_alerts = db.execute(
        select(func.count(Alert.id)).where(Alert.user_id == uid)
    ).scalar_one()
    total_episodes = db.execute(
        select(func.count(MigraineEpisode.id)).where(MigraineEpisode.user_id == uid)
    ).scalar_one()

    latest = db.execute(
        select(Prediction)
        .where(Prediction.user_id == uid)
        .order_by(Prediction.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    avg_risk = db.execute(
        select(func.avg(Prediction.risk_score)).where(Prediction.user_id == uid)
    ).scalar_one()

    band_counts = {"low": 0, "moderate": 0, "high": 0}
    predictions = db.execute(
        select(Prediction.risk_level).where(Prediction.user_id == uid)
    ).scalars().all()
    for level in predictions:
        band_counts[level] = band_counts.get(level, 0) + 1

    first_read = db.execute(
        select(func.min(SensorReading.timestamp)).where(SensorReading.user_id == uid)
    ).scalar_one_or_none()
    days = 0
    if first_read:
        days = max(0, (utcnow() - first_read).days)

    return ReportOverview(
        total_readings=total_readings,
        total_predictions=total_predictions,
        total_alerts=total_alerts,
        total_episodes=total_episodes,
        latest_risk_score=latest.risk_score if latest else None,
        latest_risk_level=latest.risk_level if latest else None,
        average_risk=round(avg_risk, 1) if avg_risk is not None else None,
        risk_band_counts=band_counts,
        days_monitored=days,
    )


def _csv_response(rows: list[list], columns: list[str], filename: str) -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(columns)
    writer.writerows(rows)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/predictions.csv")
def predictions_csv(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    predictions = (
        db.execute(
            select(Prediction)
            .where(Prediction.user_id == current.id)
            .order_by(Prediction.timestamp.desc())
        )
        .scalars()
        .all()
    )
    rows = [
        [
            p.timestamp.isoformat() if p.timestamp else "",
            p.risk_score,
            p.risk_level,
            p.prediction_window,
            p.model_version,
            p.outcome,
            p.source,
        ]
        for p in predictions
    ]
    return _csv_response(rows, ["timestamp", "risk_score", "risk_level", "prediction_window",
                                "model_version", "outcome", "source"], "predictions.csv")


@router.get("/episodes.csv")
def episodes_csv(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    episodes = (
        db.execute(
            select(MigraineEpisode)
            .where(MigraineEpisode.user_id == current.id)
            .order_by(MigraineEpisode.start_time.desc())
        )
        .scalars()
        .all()
    )
    rows = [
        [
            e.start_time.isoformat() if e.start_time else "",
            e.end_time.isoformat() if e.end_time else "",
            e.severity or "",
            ";".join(e.symptoms or []),
            e.trigger or "",
            e.notes or "",
        ]
        for e in episodes
    ]
    return _csv_response(rows, ["start_time", "end_time", "severity", "symptoms", "trigger", "notes"],
                         "episodes.csv")