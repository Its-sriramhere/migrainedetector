from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..api.deps import get_current_user
from ..core.security import utcnow
from ..db.session import get_db
from ..models import Device, SensorReading, User
from ..schemas import SensorReadingIn, SensorReadingOut, SensorReadingResponse
from ..services.prediction_service import create_prediction

router = APIRouter(prefix="/api/sensor", tags=["sensor"])


def _apply_reading(db: Session, user_id: int, body: SensorReadingIn) -> SensorReading:
    reading = SensorReading(
        user_id=user_id,
        device_id=body.device_id,
        source=body.source,
        timestamp=body.timestamp or utcnow(),
        heart_rate=body.heart_rate,
        hrv=body.hrv,
        systolic_bp=body.systolic_bp,
        diastolic_bp=body.diastolic_bp,
        spo2=body.spo2,
        temperature=body.temperature,
        activity=body.activity,
        signal_quality=body.signal_quality,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    if body.device_id:
        device = db.get(Device, body.device_id)
        if device:
            device.last_seen = utcnow()
            device.status = "online"
            db.commit()
    return reading


@router.post("/readings", response_model=SensorReadingResponse)
def post_reading(
    body: SensorReadingIn,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reading = _apply_reading(db, current.id, body)
    prediction = create_prediction(
        db, current.id, body.model_dump(), source=body.source, store_readings=False,
        device_id=body.device_id,
    )
    return SensorReadingResponse(
        reading=SensorReadingOut.model_validate(reading),
        prediction=prediction,
    )


@router.get("/latest", response_model=SensorReadingOut)
def latest_reading(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reading = db.execute(
        select(SensorReading)
        .where(SensorReading.user_id == current.id)
        .order_by(SensorReading.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()
    if reading is None:
        return SensorReadingOut(id=0, source="pi")
    return reading


@router.get("/history", response_model=list[SensorReadingOut])
def history(limit: int = 120, current: User = Depends(get_current_user),
            db: Session = Depends(get_db)):
    rows = db.execute(
        select(SensorReading)
        .where(SensorReading.user_id == current.id)
        .order_by(SensorReading.timestamp.desc())
        .limit(min(limit, 500))
    ).scalars().all()
    return list(reversed(rows))