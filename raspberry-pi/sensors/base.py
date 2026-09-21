from datetime import datetime, timezone
from typing import Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class SensorError(RuntimeError):
    pass


class BaseSensor:
    name = "base"
    available = False
    reason = "not initialized"

    def read(self) -> dict:
        raise NotImplementedError

    def is_available(self) -> bool:
        return self.available


class DemoSourceSensor(BaseSensor):
    """Fallback sensor that fabricates a realistic signal when no hardware is present."""

    name = "demo-source"
    available = True

    def __init__(self, base: Optional[dict] = None) -> None:
        import random

        self._random = random
        self._base = base or {
            "heart_rate": 74, "hrv": 46, "systolic_bp": 120, "diastolic_bp": 78,
            "spo2": 98, "temperature": 36.6, "activity": 0.45,
        }
        self._count = 0

    def read(self) -> dict:
        r = self._random
        self._count += 1
        drift = min(1.0, self._count / 40.0)
        return {
            "heart_rate": round(self._base["heart_rate"] + drift * 16 + r.uniform(-2, 2), 1),
            "hrv": round(self._base["hrv"] - drift * 18 + r.uniform(-2, 2), 1),
            "systolic_bp": round(self._base["systolic_bp"] + drift * 14 + r.uniform(-3, 3)),
            "diastolic_bp": round(self._base["diastolic_bp"] + drift * 8 + r.uniform(-2, 2)),
            "spo2": round(self._base["spo2"] - drift * 1),
            "temperature": round(self._base["temperature"] + drift * 0.3, 1),
            "activity": round(max(0.05, self._base["activity"] - drift * 0.3), 2),
            "signal_quality": round(0.9 + r.uniform(-0.05, 0.08), 2),
        }