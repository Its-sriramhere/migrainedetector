import csv
import io
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..api.deps import get_current_user
from ..core.config import settings
from ..db.session import get_db
from ..models import Prediction, SensorReading, User

router = APIRouter(prefix="/api/dataset", tags=["dataset"])

CSV_COLUMNS = [
    "timestamp", "source", "device_id", "heart_rate", "hrv",
    "systolic_bp", "diastolic_bp", "spo2", "temperature", "activity",
    "signal_quality", "risk_score", "risk_level", "prediction_window",
]


def _rows_for(user_id: int, db: Session) -> list[dict]:
    readings = (
        db.execute(
            select(SensorReading)
            .where(SensorReading.user_id == user_id)
            .order_by(SensorReading.timestamp.asc())
            .limit(settings.EXPORT_MAX_ROWS)
        )
        .scalars()
        .all()
    )

    predictions = (
        db.execute(
            select(Prediction)
            .where(Prediction.user_id == user_id)
            .order_by(Prediction.timestamp.asc())
        )
        .scalars()
        .all()
    )

    rows: list[dict] = []
    p_index = 0
    for reading in readings:
        while (p_index < len(predictions)
               and predictions[p_index].timestamp
               and reading.timestamp
               and predictions[p_index].timestamp < reading.timestamp):
            p_index += 1
        pred = predictions[p_index] if p_index < len(predictions) else None
        rows.append({
            "timestamp": reading.timestamp.isoformat() if reading.timestamp else None,
            "source": reading.source,
            "device_id": reading.device_id,
            "heart_rate": reading.heart_rate,
            "hrv": reading.hrv,
            "systolic_bp": reading.systolic_bp,
            "diastolic_bp": reading.diastolic_bp,
            "spo2": reading.spo2,
            "temperature": reading.temperature,
            "activity": reading.activity,
            "signal_quality": reading.signal_quality,
            "risk_score": pred.risk_score if pred else None,
            "risk_level": pred.risk_level if pred else None,
            "prediction_window": pred.prediction_window if pred else None,
        })
    return rows


@router.get("/export.csv")
def export_csv(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """All stored live readings (Pi + demo) as CSV, each matched with the
    risk estimate current at that moment. Ready for ML calibration."""
    rows = _rows_for(current.id, db)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    writer.writerows(rows)
    payload = buffer.getvalue()

    return StreamingResponse(
        iter([payload]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=migraine_dataset.csv"},
    )


@router.get("/export.json")
def export_json(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = _rows_for(current.id, db)
    payload = json.dumps(rows, ensure_ascii=False, indent=2)
    return StreamingResponse(
        iter([payload]),
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=migraine_dataset.json"},
    )