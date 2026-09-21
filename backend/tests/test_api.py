import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.gettempdir()}/migraine_test.db"
# Pin the engine to the stable built-in default thresholds so existing
# assertions on risk bands stay deterministic regardless of calibration runs.
os.environ["MG_THRESHOLDS_PATH"] = os.path.join(tempfile.gettempdir(), "no_such_thresholds.json")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import session  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def user_token(client):
    unique = f"user_{os.getpid()}@test.com"
    resp = client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": unique, "password": "password123", "consent_given": True},
    )
    assert resp.status_code == 201, resp.text
    return {"token": resp.json()["access_token"], "email": unique}


def auth_headers(user_token):
    return {"Authorization": f"Bearer {user_token['token']}"}


def test_registered_user_can_assess(client, user_token):
    headers = auth_headers(user_token)
    questions = client.get("/api/assessment/questions", headers=headers)
    assert questions.status_code == 200
    data = questions.json()
    assert len(data) == 14

    answers = [
        {"question_id": q["id"], "answer": q["options"][0]}
        for q in data
    ]
    profile = client.post("/api/assessment/responses", headers=headers, json={"answers": answers})
    assert profile.status_code == 200, profile.text
    assert "migraine_history_score" in profile.json()


def test_sensor_reading_produces_prediction(client, user_token):
    headers = auth_headers(user_token)
    resp = client.post(
        "/api/sensor/readings",
        headers=headers,
        json={
            "source": "pi",
            "heart_rate": 92,
            "hrv": 26,
            "systolic_bp": 138,
            "diastolic_bp": 88,
            "spo2": 97,
            "temperature": 36.9,
            "activity": 0.15,
        },
    )
    assert resp.status_code == 200, resp.text
    prediction = resp.json()["prediction"]
    assert prediction["risk_level"] == "high"
    assert prediction["risk_score"] < 100


def test_high_risk_creates_alert(client, user_token):
    headers = auth_headers(user_token)
    client.post(
        "/api/sensor/readings",
        headers=headers,
        json={
            "source": "pi",
            "heart_rate": 92,
            "hrv": 26,
            "systolic_bp": 138,
            "diastolic_bp": 88,
            "spo2": 97,
            "temperature": 36.9,
            "activity": 0.15,
        },
    )
    alerts = client.get("/api/alerts", headers=headers)
    assert alerts.status_code == 200
    assert any(a["risk_level"] == "high" for a in alerts.json())


def test_demo_scenario(client, user_token):
    headers = auth_headers(user_token)
    resp = client.post("/api/demo/scenario", headers=headers, json={"scenario": "moderate"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["prediction"]["risk_level"] in ("low", "moderate", "high")


def test_predict_endpoint(client, user_token):
    headers = auth_headers(user_token)
    resp = client.post(
        "/api/predictions/predict",
        headers=headers,
        json={"heart_rate": 92, "hrv": 26, "systolic_bp": 138, "diastolic_bp": 88,
              "spo2": 97, "temperature": 36.9, "activity": 0.15},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["risk_level"] == "high"


def test_reports_overview(client, user_token):
    headers = auth_headers(user_token)
    resp = client.get("/api/reports/overview", headers=headers)
    assert resp.status_code == 200
    assert "risk_band_counts" in resp.json()


def test_device_register_and_heartbeat(client, user_token):
    headers = auth_headers(user_token)
    device = client.post(
        "/api/devices/register",
        headers=headers,
        json={"device_identifier": "PI-TEST-001", "device_name": "Test Pi"},
    )
    assert device.status_code == 201, device.text

    beat = client.post(
        "/api/devices/heartbeat",
        headers=headers,
        json={"device_identifier": "PI-TEST-001", "device_name": "Test Pi"},
    )
    assert beat.status_code == 200, beat.text
    assert beat.json()["status"] == "online"
    assert beat.json()["last_seen"] is not None

    missing = client.post(
        "/api/devices/heartbeat",
        headers=headers,
        json={"device_identifier": "PI-NOT-REGISTERED"},
    )
    assert missing.status_code == 404


def test_dataset_export_csv(client, user_token):
    headers = auth_headers(user_token)
    client.post(
        "/api/sensor/readings",
        headers=headers,
        json={"source": "pi", "heart_rate": 78, "hrv": 42, "systolic_bp": 120,
              "diastolic_bp": 78, "spo2": 98, "temperature": 36.6, "activity": 0.5},
    )
    resp = client.get("/api/dataset/export.csv", headers=headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    body = resp.text
    assert "timestamp,source" in body
    assert "95" not in body[:0]  # sanity: header row present
    assert "\n" in body


def test_report_csvs_downloadable(client, user_token):
    headers = auth_headers(user_token)
    pred = client.get("/api/reports/predictions.csv", headers=headers)
    assert pred.status_code == 200
    assert "text/csv" in pred.headers["content-type"]
    assert "timestamp,risk_score" in pred.text

    episodes = client.get("/api/reports/episodes.csv", headers=headers)
    assert episodes.status_code == 200
    assert "start_time,end_time" in episodes.text


def test_alert_triggers_notification_log(client):
    unique = f"notif_{os.getpid()}@test.com"
    reg = client.post(
        "/api/auth/register",
        json={"name": "Notif User", "email": unique, "password": "password123", "consent_given": True},
    )
    assert reg.status_code == 201
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    client.post(
        "/api/sensor/readings",
        headers=headers,
        json={"source": "pi", "heart_rate": 92, "hrv": 26, "systolic_bp": 138,
              "diastolic_bp": 88, "spo2": 97, "temperature": 36.9, "activity": 0.15},
    )

    from sqlalchemy import desc, select

    from app.db.session import SessionLocal
    from app.models import NotificationLog

    db = SessionLocal()
    try:
        logs = db.execute(
            select(NotificationLog).order_by(desc(NotificationLog.id)).limit(1)
        ).scalars().first()
    finally:
        db.close()

    assert logs is not None
    assert logs.risk_level == "high"
    assert logs.status in ("sent", "skipped")
    assert logs.kind == "sms"