"""MAX30205 (or compatible) body-temperature-oriented sensor."""
from __future__ import annotations

from .base import BaseSensor


class TemperatureSensor(BaseSensor):
    name = "temperature"
    available = False

    def __init__(self, simulated: bool = False) -> None:
        self.simulated = simulated
        if simulated:
            self.available = True

    def read(self) -> dict:
        if not self.available:
            return {"temperature": None}
        return {"temperature": 36.6}