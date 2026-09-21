import asyncio
from typing import Any, Optional

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from ..api.deps import get_current_user
from ..core.config import settings
from ..db.session import SessionLocal, get_db
from ..ml.heuristic_engine import demo_signal_for_scenario, interpolate_signals
from ..models import User
from ..schemas import (
    DemoSensorData,
    DemoScenarioRequest,
    DemoSessionStatus,
    DemoStartResponse,
    SensorReadingOut,
    SensorReadingResponse,
)
from ..services.prediction_service import create_prediction

router = APIRouter(prefix="/api/demo", tags=["demo"])


def _app_state(request: Request) -> dict[str, Any]:
    state = getattr(request.app.state, "demo", None)
    if state is None:
        state = {}
        request.app.state.demo = state
    return state


@router.get("/status", response_model=DemoSessionStatus)
def demo_status(request: Request, current: User = Depends(get_current_user)):
    tasks = _app_state(request).get("scenarios", {})
    return DemoSessionStatus(running=current.id in tasks, scenario=(
        tasks[current.id].get("scenario") if current.id in tasks else None))


def _reading_out(signal: dict) -> SensorReadingOut:
    return SensorReadingOut(
        id=0,
        source="demo",
        timestamp=None,
        heart_rate=signal.get("heart_rate"),
        hrv=signal.get("hrv"),
        systolic_bp=signal.get("systolic_bp"),
        diastolic_bp=signal.get("diastolic_bp"),
        spo2=signal.get("spo2"),
        temperature=signal.get("temperature"),
        activity=signal.get("activity"),
        signal_quality=signal.get("signal_quality"),
    )


@router.post("/scenario", response_model=SensorReadingResponse)
def send_scenario(
    body: DemoScenarioRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    signal = demo_signal_for_scenario(body.scenario)
    prediction = create_prediction(db, current.id, signal, source="demo")
    return SensorReadingResponse(reading=_reading_out(signal), prediction=prediction)


@router.post("/sensor-data", response_model=SensorReadingResponse)
def send_demo_sensor(body: DemoSensorData, db: Session = Depends(get_db),
                     current: User = Depends(get_current_user)):
    from ..api.sensor import _apply_reading
    reading = _apply_reading(db, current.id, body)
    prediction = create_prediction(db, current.id, body.model_dump(), source="demo",
                                   store_readings=False)
    return SensorReadingResponse(reading=reading, prediction=prediction)


async def _run_stream(user_id: int, scenario: str, start_signal: Optional[dict] = None) -> None:
    from ..db.session import SessionLocal as SL

    normal = demo_signal_for_scenario("normal")
    moderate = demo_signal_for_scenario("moderate")
    high = demo_signal_for_scenario("high")

    if start_signal:
        # Continue from the caller's configured values, settling toward the scenario target.
        if scenario == "normal":
            stream = interpolate_signals(start_signal, normal, 8) + interpolate_signals(normal, normal, 12) * 4
        elif scenario == "moderate":
            stream = interpolate_signals(start_signal, moderate, 8) + interpolate_signals(moderate, moderate, 8) * 2
        else:
            stream = interpolate_signals(start_signal, high, 8) + interpolate_signals(high, high, 6) * 3
    elif scenario == "normal":
        stream = interpolate_signals(normal, normal, 12) * 4
    elif scenario == "moderate":
        stream = interpolate_signals(normal, moderate, 14) + interpolate_signals(moderate, moderate, 8) * 2
    else:
        stream = interpolate_signals(normal, high, 18) + interpolate_signals(high, high, 6) * 3

    try:
        for point in stream:
            with SL() as db:
                create_prediction(db, user_id, point, source="demo")
            await asyncio.sleep(settings.DEMO_INTERVAL_SECONDS)
    except asyncio.CancelledError:
        return


@router.post("/start", response_model=DemoStartResponse)
async def start_demo(body: DemoScenarioRequest, request: Request,
                     db: Session = Depends(get_db),
                     current: User = Depends(get_current_user)):
    tasks = _app_state(request).setdefault("scenarios", {})
    existing = tasks.get(current.id)
    if existing:
        existing.get("task").cancel()

    immediate = None
    if body.signal:
        # Validate + create the first prediction synchronously so the risk state
        # (and any SMS) fires the moment the user clicks Start.
        signal = {k: v for k, v in body.signal.items() if v is not None}
        prediction = create_prediction(db, current.id, signal, source="demo")
        immediate = SensorReadingResponse(reading=_reading_out(signal), prediction=prediction)

    task = asyncio.create_task(_run_stream(current.id, body.scenario, body.signal))
    tasks[current.id] = {"task": task, "scenario": body.scenario}
    task.add_done_callback(lambda _t: tasks.pop(current.id, None))
    return DemoStartResponse(
        running=True,
        scenario=body.scenario,
        reading=immediate.reading if immediate else None,
        prediction=immediate.prediction if immediate else None,
    )


@router.post("/stop")
async def stop_demo(request: Request, current: User = Depends(get_current_user)):
    tasks = _app_state(request).get("scenarios", {})
    entry = tasks.pop(current.id, None)
    if entry:
        entry.get("task").cancel()
    return DemoSessionStatus(running=False, scenario=None)