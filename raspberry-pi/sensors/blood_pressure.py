"""Blood-pressure module (periodic measurements).

BP is treated as a periodic measurement. If the module exposes an analog
signal an ADS1115 (or compatible ADC) is used because the Raspberry Pi GPIO
header provides no general-purpose analog input.
"""
from __future__ import annotations

from .base import BaseSensor


class BloodPressureSensor(BaseSensor):
    name = "blood_pressure"
    available = False

    def __init__(self, simulated: bool = False) -> None:
        self.simulated = simulated
        if simulated:
            self.available = True

    def read(self) -> dict:
        if not self.available:
            return {"systolic_bp": None, "diastolic_bp": None}
        return {"systolic_bp": 120.0, "diastolic_bp": 78.0}