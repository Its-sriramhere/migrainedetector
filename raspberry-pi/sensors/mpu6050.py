"""MPU6050 accelerometer/IMU activity sensor."""
from __future__ import annotations

import math
from typing import Optional

from .base import BaseSensor

try:
    import smbus2  # type: ignore
except ImportError:
    smbus2 = None


class MPU6050Sensor(BaseSensor):
    name = "mpu6050"
    available = False

    def __init__(self, bus: int = 1, address: int = 0x68, simulated: bool = False) -> None:
        self.address = address
        self.simulated = simulated
        if simulated:
            self.available = True
            return
        if smbus2 is None:
            return
        try:
            self._i2c = smbus2.SMBus(bus)
            self._i2c.write_byte_data(address, 0x6B, 0x00)  # wake
            self.available = True
        except Exception as exc:  # pragma: no cover - hardware only
            self._i2c = None
            self.reason = str(exc)

    def _raw(self) -> Optional[tuple[float, float, float]]:
        if not self.available:
            return None
        data = self._i2c.read_i2c_block_data(self.address, 0x3B, 6)  # ACCEL_XOUT_H
        def signed(hi: int, lo: int) -> int:
            val = (hi << 8) | lo
            return val - 65536 if val >= 32768 else val
        return (signed(data[0], data[1]), signed(data[2], data[3]), signed(data[4], data[5]))

    def read(self) -> dict:
        raw = self._raw()
        if raw is None:
            if self.simulated:
                return {"activity": 0.45}
            return {"activity": None}
        magnitude = math.sqrt(sum(v * v for v in raw))
        normalized = min(1.0, magnitude / 20000.0)
        return {"activity": round(normalized, 3)}