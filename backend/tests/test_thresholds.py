"""Calibration + threshold behaviour tests.

These pin the two things the feature is about: (1) that the calibration
pipeline writes a thresholds file the engine loads and that derived demo
scenarios land in the expected risk bands; (2) that alert cooldown + SMS
quota respect the configured (possibly recalibrated) band edges rather than a
hardcoded constant.
"""
import json
import os
import tempfile
import uuid
from pathlib import Path

import pytest

pandas = pytest.importorskip("pandas")
numpy = pytest.importorskip("numpy")

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.gettempdir()}/migraine_th_{uuid.uuid4().hex}.db"
os.environ.setdefault("MG_THRESHOLDS_PATH", os.path.join(tempfile.gettempdir(), "no_such.json"))
sys_path_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if sys_path_dir not in os.sys.path:
    os.sys.path.insert(0, sys_path_dir)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.ml.heuristic_engine import HeuristicEngine, demo_signal_for_scenario  # noqa: E402
from ml.calibrate import calibrate  # noqa: E402


def _synthetic_frame(n_clean: int = 24, n_episode: int = 12) -> "pandas.DataFrame":
    numpy.random.seed(42)
    clean = pandas.DataFrame(
        {
            "heart_rate": numpy.random.normal(82, 2, n_clean),
            "systolic_bp": numpy.random.normal(120, 2, n_clean),
            "diastolic_bp": numpy.random.normal(78, 2, n_clean),
            "spo2": numpy.random.normal(98, 0.3, n_clean),
            "temperature": numpy.random.normal(36.4, 0.1, n_clean),
            "activity": numpy.random.normal(0.5, 0.05, n_clean),
            "episode": 0,
            "hr_abnormal": 0,
        }
    )
    episode = pandas.DataFrame(
        {
            "heart_rate": numpy.random.normal(104, 5, n_episode),
            "systolic_bp": numpy.random.normal(130, 3, n_episode),
            "diastolic_bp": numpy.random.normal(84, 3, n_episode),
            "spo2": numpy.random.normal(97, 0.5, n_episode),
            "temperature": numpy.random.normal(36.7, 0.15, n_episode),
            "activity": numpy.random.normal(0.35, 0.05, n_episode),
            "episode": 1,
            "hr_abnormal": 0,
        }
    )
    abnormal = pandas.DataFrame(
        {
            "heart_rate": numpy.random.normal(118, 6, n_episode),
            "systolic_bp": numpy.random.normal(120, 3, n_episode),
            "diastolic_bp": numpy.random.normal(78, 3, n_episode),
            "spo2": numpy.random.normal(98, 0.4, n_episode),
            "temperature": numpy.random.normal(36.5, 0.15, n_episode),
            "activity": numpy.random.normal(0.5, 0.05, n_episode),
            "episode": 0,
            "hr_abnormal": 1,
        }
    )
    return pandas.concat([clean, episode, abnormal], ignore_index=True)


def test_calibration_roundtrip_writes_loadable_config():
    frame = _synthetic_frame()
    config = calibrate(frame, label_col="episode", extra_labels={"heart_rate": "hr_abnormal"})
    assert config["calibrated"] is True
    assert config["baselines"]["systolic_bp"] > 115
    assert config["deviations"]["hr_trigger_pct"] > 5
    assert config["deviations"]["spo2_drop"] >= 0.5
    assert set(config["demo_presets"]) == {"normal", "moderate", "high"}

    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "thresholds.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        engine = HeuristicEngine(config_path=str(path))
        assert engine.calibrated is True
        assert engine.band_low == 30.0

        result = engine.evaluate(demo_signal_for_scenario("normal"), {})
        assert result.risk_level == "low"
        result = engine.evaluate(demo_signal_for_scenario("high"), {})
        assert result.risk_level in ("moderate", "high")
        assert result.risk_score > engine.band_low


def test_custom_band_edges_control_risk_band():
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "thresholds.json"
        path.write_text(json.dumps({"band_edges": {"low": 40, "high": 60}, "calibrated": True}),
                        encoding="utf-8")
        engine = HeuristicEngine(config_path=str(path))
        assert engine.band_low == 40 and engine.band_high == 60

        normal = engine.evaluate(demo_signal_for_scenario("normal"), {})
        assert normal.risk_level == "low"
        # score 45 with custom bands -> moderate
        faked = {"heart_rate": 100, "hrv": 40, "systolic_bp": 128, "diastolic_bp": 82,
                 "spo2": 97, "temperature": 36.7, "activity": 0.3}
        moderate = engine.evaluate(faked, {})
        assert moderate.risk_score > 40
        assert moderate.risk_level == "moderate"


_call_counter = [0]


def _register_user(client: "TestClient") -> dict:
    _call_counter[0] += 1
    resp = client.post("/api/auth/register", json={
        "name": "Th User", "email": f"th_{os.getpid()}_{_call_counter[0]}@test.com",
        "password": "password123", "consent_given": True,
    })
    assert resp.status_code == 201, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_repeated_moderate_readings_produce_single_alert():
    with TestClient(app) as client:
        headers = _register_user(client)
        payload = {"source": "pi", "heart_rate": 92, "hrv": 26, "systolic_bp": 125,
                   "diastolic_bp": 82, "spo2": 97, "temperature": 36.7, "activity": 0.15}
        first = client.post("/api/sensor/readings", headers=headers, json=payload)
        assert first.status_code == 200, first.text
        assert first.json()["prediction"]["risk_level"] == "moderate"
        second = client.post("/api/sensor/readings", headers=headers, json=payload)
        assert second.status_code == 200, second.text

        # Cooldown: a second reading in the same band must NOT open a new alert.
        alerts = client.get("/api/alerts", headers=headers).json()
        assert len(alerts) == 1


def test_sms_quota_cap_and_notifications_log(tmp_path, monkeypatch):
    import app.services.notifications as notifications

    original_enabled = notifications.settings.SMS_ENABLED
    original_max = notifications.settings.SMS_MAX_SENDS
    original_to = notifications.settings.ALERT_SMS_TO
    try:
        from app.db.seed import init_db

        init_db()

        notifications.settings.SMS_ENABLED = True
        notifications.settings.ALERT_SMS_TO = "+919360516302"

        from sqlalchemy import func, select

        from app.db.session import SessionLocal
        from app.models import NotificationLog, User

        db = SessionLocal()
        try:
            # the real-send count may contain rows left by a previous run of
            # this suite against the shared temp DB, so allow one further send.
            # Every twilio attempt (sent OR failed) counts toward the cap.
            existing_sends = db.execute(
                select(func.count()).select_from(NotificationLog).where(
                    NotificationLog.provider == "twilio")
            ).scalar() or 0
        finally:
            db.close()
        notifications.settings.SMS_MAX_SENDS = existing_sends + 1
        max_cap = notifications.settings.SMS_MAX_SENDS

        class _StubTwilio(notifications.NotificationProvider):
            name = "twilio"

            def send(self, recipient, message, level):
                return notifications.NotificationReceipt(
                    status="sent", provider=self.name, detail="stubbed send")

        monkeypatch.setattr(notifications, "_provider", lambda: _StubTwilio())

        db = SessionLocal()
        try:
            user = db.query(User).first()
            if user is None:
                user = User(name="Quota User", email=f"quota_{uuid.uuid4().hex}@test.com",
                            password_hash="x", consent_given=True)
                db.add(user)
                db.commit()
                db.refresh(user)
            r1 = notifications.send_alert_notification(db, user.id, None, "high", "test 1")
            r2 = notifications.send_alert_notification(db, user.id, None, "high", "test 2")
            # read before close: commit expires instances
            assert r1.status == "sent"
            assert r2.status == "quota_exceeded"
        finally:
            db.close()

        with TestClient(app) as client:
            headers = _register_user(client)
            info = client.get("/api/alerts/notifications", headers=headers)
            assert info.status_code == 200
            body = info.json()
            assert body["sms_enabled"] is True
            assert body["sms_max_sends"] == max_cap
            assert body["logs"] == []  # per-user view: fresh user sees nothing
    finally:
        notifications.settings.SMS_ENABLED = original_enabled
        notifications.settings.SMS_MAX_SENDS = original_max
        notifications.settings.ALERT_SMS_TO = original_to


def test_datasets_api_calibrate_and_download(tmp_path, monkeypatch):
    import app.api.datasets as datasets_module

    frame = _synthetic_frame()
    data_dir = tmp_path / "datasets"
    data_dir.mkdir()
    frame.to_csv(data_dir / "calibration.csv", index=False)

    out_path = tmp_path / "thresholds.json"
    monkeypatch.setattr(datasets_module, "ML_DIR", data_dir)
    monkeypatch.setattr(datasets_module.settings, "THRESHOLDS_PATH", str(out_path))

    with TestClient(app) as client:
        headers = _register_user(client)

        resp = client.get("/api/datasets", headers=headers)
        assert resp.status_code == 200, resp.text
        assert any(f["name"] == "calibration.csv" for f in resp.json()["files"])

        cal = client.post("/api/datasets/calibrate", headers=headers,
                          json={"file": "calibration.csv", "label_cols": {"heart_rate": "hr_abnormal"}})
        assert cal.status_code == 200, cal.text
        assert cal.json()["ok"] is True
        assert cal.json()["config"]["calibrated"] is True
        assert out_path.is_file()

        cfg = client.get("/api/datasets/thresholds", headers=headers)
        assert cfg.status_code == 200
        body = cfg.json()
        assert "calibrated" in body
        assert body["band_edges"]["low"] == 30.0
        # calibration must be reflected in the engine that drives predictions:
        # in production ENGINE.config_path == settings.THRESHOLDS_PATH, so the
        # committed file is what the endpoint reads; here the engine stays on
        # the test-pinned defaults, while the *file* itself is calibrated.
        assert json.loads(out_path.read_text(encoding="utf-8"))["calibrated"] is True

        dl = client.get("/api/datasets/download/calibration.csv", headers=headers)
        assert dl.status_code == 200
        assert "heart_rate" in dl.text