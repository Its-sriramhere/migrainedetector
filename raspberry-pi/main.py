"""Migraine Detector edge application for the Raspberry Pi.

Collects physiological readings, validates and filters them, stores them in a
local SQLite buffer, and uploads to the backend. Runs as a demo sensor source
when no hardware is present.
"""
from __future__ import annotations

import time

from communication.api_client import APIClient
from config import settings
from monitoring.device_health import DeviceHealth
from processing.filtering import MovingMedianFilter, build_pipeline
from processing.features import WindowFeatureExtractor
from processing.signal_quality import check_signal, is_trusted
from sensors.base import DemoSourceSensor
from sensors.blood_pressure import BloodPressureSensor
from sensors.max30102 import MAX30102Sensor
from sensors.mpu6050 import MPU6050Sensor
from sensors.temperature import TemperatureSensor
from storage.local_database import LocalDatabase


def build_sensors() -> list:
    sensors = [
        MAX30102Sensor(),
        BloodPressureSensor(simulated=True),
        TemperatureSensor(simulated=True),
        MPU6050Sensor(simulated=True),
    ]
    if settings.DEMO_SOURCE_ENABLED:
        sensors.append(DemoSourceSensor())
    return sensors


def main() -> None:
    health = DeviceHealth()
    api = APIClient()
    db = LocalDatabase(settings.LOCAL_DB)
    pipeline = build_pipeline([check_signal])
    extractor = WindowFeatureExtractor(window=5)
    hr_filter = MovingMedianFilter(5)
    last_beat = 0.0

    sensors = build_sensors()
    health.summary(sensors)

    if settings.AUTH_TOKEN:
        api.register_device(settings.DEVICE_NAME)

    print("Migraine Detector edge app started.")
    try:
        while True:
            now = time.time()
            if now - last_beat >= settings.HEARTBEAT_INTERVAL:
                api.heartbeat()
                last_beat = now

            combined: dict = {}
            for sensor in sensors:
                combined.update(sensor.read())
            combined["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
            combined["device"] = settings.DEVICE_ID

            cleaned = pipeline(combined)
            if not is_trusted(cleaned):
                print("Dropping untrusted sample:", cleaned)
                health.heartbeat()
                time.sleep(settings.UPLOAD_INTERVAL)
                continue

            if combined.get("heart_rate") is not None:
                cleaned["heart_rate"] = hr_filter.filter(cleaned["heart_rate"])
            cleaned = extractor.add(cleaned)

            db.save(cleaned)
            pending = db.pending(50)
            uploaded_ids = []
            for sample in pending:
                if api.upload(sample):
                    uploaded_ids.append(sample["id"])
            db.mark_uploaded(uploaded_ids)
            health.heartbeat()

            if pending:
                print(
                    f"Stored {len(pending)} readings; uploaded {len(uploaded_ids)}; "
                    f"buffer={db.stats()}"
                )
            time.sleep(settings.UPLOAD_INTERVAL)
    except KeyboardInterrupt:
        print("Shutting down.")
    finally:
        db.close()


if __name__ == "__main__":
    main()