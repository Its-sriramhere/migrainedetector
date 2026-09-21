from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from .api import (alerts, assessment, auth, dataset, datasets, demo, devices,
                  migraine, predictions, reports, sensor, users)
from .core.config import settings
from .db.seed import init_db, seed_questions
from .db.session import SessionLocal
from .models import User
from .websocket.manager import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_questions(db)
    finally:
        db.close()
    app.state.demo = {}
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "Personalized IoT migraine early-warning platform. "
        "Research prototype — estimates risk; not a medical diagnostic device."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    auth.router,
    users.router,
    assessment.router,
    devices.router,
    sensor.router,
    predictions.router,
    migraine.router,
    alerts.router,
    demo.router,
    reports.router,
    dataset.router,
    datasets.router,
):
    app.include_router(router)


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "docs": "/docs",
        "message": "Migraine risk early-warning API — research prototype.",
    }


def _user_from_token(websocket: WebSocket) -> User | None:
    from .core.security import decode_access_token

    token = websocket.query_params.get("token")
    if not token:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    db = SessionLocal()
    try:
        return db.execute(
            select(User).where(User.id == int(payload["sub"]))
        ).scalar_one_or_none()
    finally:
        db.close()


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    user = _user_from_token(websocket)
    if user is None or user.id != user_id:
        await websocket.close(code=4401)
        return
    await manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception:
        manager.disconnect(user_id, websocket)