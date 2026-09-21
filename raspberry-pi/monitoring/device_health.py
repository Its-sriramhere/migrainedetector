"""Reports device health: which sensors are available and last heartbeat."""
from __future__ import annotations

from datetime import datetime, timezone


class DeviceHealth:
    def __init__(self) -> None:
        self.started = datetime.now(timezone.utc)
        self.last_heartbeat = self.started

    def heartbeat(self) -> None:
        self.last_heartbeat = datetime.now(timezone.utc)

    def summary(self, sensors: list) -> dict:
        return {
            "uptime_seconds": int((datetime.now(timezone.utc) - self.started).total_seconds()),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "sensors": [
                {"name": s.name, "available": s.is_available(), "reason": getattr(s, "reason", None)}
                for s in sensors
            ],
        }