"""Feature extraction: pairs a raw reading with a short-window baseline."""


class WindowFeatureExtractor:
    def __init__(self, window: int = 5) -> None:
        from collections import deque

        self.window = window
        self._history: dict[str, deque] = {k: deque(maxlen=window) for k in (
            "heart_rate", "hrv", "systolic_bp", "diastolic_bp", "spo2", "temperature", "activity",
        )}

    def add(self, sample: dict) -> dict:
        out = dict(sample)
        for key, deque_ in self._history.items():
            value = sample.get(key)
            if value is None:
                continue
            deque_.append(value)
            values = list(deque_)
            out[f"{key}_baseline"] = round(sum(values) / len(values), 2)
            out[f"{key}_dev"] = round(value - out[f"{key}_baseline"], 2)
        return out


def extract(sample: dict, history: dict[str, list[float]] | None = None) -> dict:
    """Lifestyle-agnostic feature extraction against a provided history."""
    out = dict(sample)
    history = history or {}
    for key, values in history.items():
        if values:
            mean = sum(values) / len(values)
            out[f"{key}_baseline"] = round(mean, 2)
            out[f"{key}_dev"] = round((sample.get(key) or 0) - mean, 2)
    return out