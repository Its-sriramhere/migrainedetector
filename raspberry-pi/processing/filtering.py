"""Simple smoothing filters applied to physiological samples."""
from __future__ import annotations

from collections import deque
from typing import Callable, Optional


class MovingMedianFilter:
    def __init__(self, window: int = 5) -> None:
        self.window = max(1, window)
        self._buffer: deque[float] = deque(maxlen=self.window)

    def filter(self, value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        self._buffer.append(value)
        ordered = sorted(self._buffer)
        n = len(ordered)
        return ordered[n // 2]

    def reset(self) -> None:
        self._buffer.clear()


def clamp(value: Optional[float], lo: float, hi: float) -> Optional[float]:
    if value is None:
        return None
    return max(lo, min(hi, value))


def build_pipeline(
    checks: Optional[list[Callable[[dict], dict]]] = None,
) -> Callable[[dict], dict]:
    """Chains sensor reads through signal-quality checks and cleaning steps."""

    def run(sample: dict) -> dict:
        out = dict(sample)
        for check in checks or []:
            out = check(out)
        return out

    return run