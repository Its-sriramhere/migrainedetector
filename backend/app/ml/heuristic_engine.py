from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Optional

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "thresholds.json")
CONFIG_PATH_ENV = "MG_THRESHOLDS_PATH"

DEFAULT_CONFIG: dict = {
    "band_edges": {"low": 30, "high": 70},
    "deviations": {
        "static_floor": 8.0,
        # heart-rate rise above baseline (%): trigger + weight per extra %
        "hr_trigger_pct": 5.0,
        "hr_weight": 0.9,
        # HRV drop below baseline (%): trigger + weight per extra %
        "hrv_trigger_pct": -5.0,
        "hrv_weight": 0.8,
        # blood-pressure rise above baseline (%): trigger + weight
        "bp_trigger_pct": 3.0,
        "bp_weight": 0.6,
        # SpO2 drop below baseline
        "spo2_drop": 1.0,
        "spo2_contribution": 5.0,
        # temperature absolute deviation
        "temp_dev": 0.6,
        "temp_weight": 3.0,
        "temp_cap": 6.0,
        # activity absolute deviation factor of baseline
        "activity_dev_factor": 0.35,
        "activity_weight": 4.0,
        "activity_cap": 6.0,
        # static lifestyle components
        "sleep_weight": 0.8,
        "sleep_cap": 10.0,
        "stress_weight": 0.6,
        "stress_cap": 8.0,
        "trigger_weight": 0.9,
        "trigger_cap": 6.0,
    },
}

# Add all band keys referenced by the UI/docs.
RESERVED_STATIC = [
    "static_floor", "hr_trigger_pct", "hr_weight", "hrv_trigger_pct", "hrv_weight",
    "bp_trigger_pct", "bp_weight", "spo2_drop", "spo2_contribution",
    "temp_dev", "temp_weight", "temp_cap", "activity_dev_factor", "activity_weight",
    "activity_cap", "sleep_weight", "sleep_cap", "stress_weight", "stress_cap",
    "trigger_weight", "trigger_cap",
]

SIGNAL_QUALITY_BY_SCENARIO = {"normal": 0.98, "moderate": 0.95, "high": 0.92}


def _load_config(config_path: Optional[str] = None) -> tuple[dict, bool]:
    """Return (config, calibrated). Recognizes ml/calibrate.py output."""
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    path = config_path or CONFIG_PATH
    if not os.path.exists(path):
        return cfg, False
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        band = cfg["band_edges"]
        band.update(data.get("band_edges", {}))
        dev = cfg["deviations"]
        dev.update(data.get("deviations", {}))
        for key in ("baselines", "demo_presets", "source_data"):
            if key in data:
                cfg[key] = data[key]
        return cfg, data.get("calibrated", False)
    except (OSError, ValueError) as exc:  # noqa: BLE001
        print(f"HeuristicEngine: ignoring bad {path}: {exc}")
        return cfg, False


@dataclass
class RiskFactors:
    migraine_frequency_score: float = 0.0
    stress_score: float = 0.0
    sleep_irregularity: float = 0.0
    sleep_deviation: float = 0.0
    trigger_load: float = 0.0
    hydration_deviation: float = 0.0
    caffeine_deviation: float = 0.0


@dataclass
class Baseline:
    heart_rate: float = 72.0
    hrv: float = 48.0
    systolic_bp: float = 118.0
    diastolic_bp: float = 76.0
    spo2: float = 98.0
    temperature: float = 36.5
    activity: float = 0.5


@dataclass
class FeatureAttribution:
    feature_name: str
    feature_value: float
    contribution: float


@dataclass
class RiskResult:
    risk_score: float
    risk_level: str
    contributions: list[FeatureAttribution] = field(default_factory=list)


def risk_level(score: float, band_low: float = 30.0, band_high: float = 70.0) -> str:
    if score < band_low:
        return "low"
    if score <= band_high:
        return "moderate"
    return "high"


def _rel(pct: Optional[float]) -> float:
    return pct if pct is not None else 0.0


class HeuristicEngine:
    """Deterministic risk-scoring engine.

    Loads `thresholds.json` (written by ``ml/calibrate.py``) when present, so
    deviation cutoffs, weights and band edges can be derived from a real migraine
    dataset. Falls back to built-in heuristics when the file is missing.

    The config is hot-reloaded: a change to the thresholds file (e.g. via
    ``POST /api/datasets/calibrate``) is picked up on the next evaluation
    without restarting the server.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        if config_path is None:
            config_path = os.environ.get(CONFIG_PATH_ENV)
        if config_path is None:
            try:
                from ..core.config import settings
                config_path = settings.THRESHOLDS_PATH
            except Exception:  # noqa: BLE001 - standalone use
                config_path = CONFIG_PATH
        self.config_path = config_path
        self._mtime: Optional[float] = None
        self._load()

    def _load(self) -> None:
        cfg, calibrated = _load_config(self.config_path)
        band = cfg["band_edges"]
        self.band_low = float(band.get("low", 30.0))
        self.band_high = float(band.get("high", 70.0))
        self.deviations = cfg["deviations"]
        self.calibrated = calibrated
        self.model_version = "heuristic-calibrated-v1" if calibrated else "heuristic-v1"
        self.baselines = cfg.get("baselines", {})
        self.demo_presets = cfg.get("demo_presets", {})
        self.source_data = cfg.get("source_data") or ""
        try:
            self._mtime = os.stat(self.config_path).st_mtime
        except OSError:
            self._mtime = None

    def reload(self) -> None:
        """Force reload of the thresholds file (used after recalibration)."""
        self._mtime = None
        self._load()

    def _reload_if_changed(self) -> None:
        if not os.path.exists(self.config_path):
            return
        try:
            mtime = os.stat(self.config_path).st_mtime
        except OSError:
            return
        if mtime != self._mtime:
            self._load()

    def _band(self) -> list[float]:
        return [self.band_low, self.band_high]

    def config_snapshot(self) -> dict:
        """Serialize current configuration for the datasets API / UI."""
        return {
            "calibrated": self.calibrated,
            "model_version": self.model_version,
            "source_data": self.source_data,
            "band_edges": {"low": self.band_low, "high": self.band_high},
            "deviations": dict(self.deviations),
            "baselines": dict(self.baselines),
            "demo_presets": dict(self.demo_presets),
        }

    def signal_for_scenario(self, scenario: str) -> dict:
        """Dataset-derived signal preset for the simulation, if calibrated."""
        preset = self.demo_presets.get(scenario)
        if not preset:
            return demo_signal_for_scenario(scenario)
        signal = dict(preset)
        signal.setdefault("signal_quality", SIGNAL_QUALITY_BY_SCENARIO.get(scenario, 0.95))
        return signal

    def evaluate(
        self,
        signal: dict,
        baseline: Baseline | None = None,
        factors: RiskFactors | None = None,
    ) -> RiskResult:
        self._reload_if_changed()
        b = baseline or Baseline()
        f = factors or RiskFactors()
        dev = self.deviations

        hr = signal.get("heart_rate")
        hrv = signal.get("hrv")
        sbp = signal.get("systolic_bp")
        dbp = signal.get("diastolic_bp")
        spo2 = signal.get("spo2")
        temp = signal.get("temperature")
        act = signal.get("activity")

        score = dev.get("static_floor", 8.0) * 1.0
        contributions: list[FeatureAttribution] = []

        static = f.migraine_frequency_score + f.stress_score + f.sleep_irregularity
        static += min(8.0, f.trigger_load * 1.5)
        static += min(6.0, f.sleep_deviation * 2.0)
        if f.hydration_deviation > 0:
            static += min(4.0, f.hydration_deviation * 3.0)
        if f.caffeine_deviation > 0:
            static += min(4.0, f.caffeine_deviation * 3.0)
        score += static

        def add(name: str, value: float, amount: float) -> None:
            nonlocal score
            amount = max(0.0, amount)
            score += amount
            contributions.append(FeatureAttribution(name, round(value, 2), round(amount, 2)))

        hr_dev = hr_rel = hrv_dev = hrv_rel = 0.0
        if hr is not None and b.heart_rate:
            hr_rel = (hr - b.heart_rate) * 100.0 / b.heart_rate
            hr_dev = hr - b.heart_rate
            trigger = dev.get("hr_trigger_pct", 5.0)
            if hr_rel > trigger:
                add("HR_increase", hr_rel, (hr_rel - trigger) * dev.get("hr_weight", 0.9))
        if hrv is not None and b.hrv:
            hrv_rel = (hrv - b.hrv) * 100.0 / b.hrv
            hrv_dev = hrv - b.hrv
            trigger = dev.get("hrv_trigger_pct", -5.0)
            if hrv_rel < trigger:
                add("HRV_decrease", hrv_rel, (-hrv_rel - (-trigger)) * dev.get("hrv_weight", 0.8))

        bp_rel = 0.0
        if sbp is not None and b.systolic_bp and b.systolic_bp > 0:
            bp_rel = max(
                (sbp - b.systolic_bp) * 100.0 / b.systolic_bp,
                ((dbp or 0) - b.diastolic_bp) * 100.0 / b.diastolic_bp if b.diastolic_bp else 0,
            )
            trigger = dev.get("bp_trigger_pct", 3.0)
            if bp_rel > trigger:
                add("BP_variation", bp_rel, (bp_rel - trigger) * dev.get("bp_weight", 0.6))

        if spo2 is not None and b.spo2:
            drop = dev.get("spo2_drop", 1.0)
            if spo2 < b.spo2 - drop:
                add("SpO2_drop", spo2 - b.spo2, dev.get("spo2_contribution", 5.0))

        if temp is not None and b.temperature:
            t_dev = abs(temp - b.temperature)
            trigger = dev.get("temp_dev", 0.6)
            if t_dev > trigger:
                add("Temperature_change", temp - b.temperature,
                    min(dev.get("temp_cap", 6.0), (t_dev - trigger) * dev.get("temp_weight", 3.0)))

        if act is not None and b.activity is not None:
            a_dev = abs(act - b.activity)
            threshold = dev.get("activity_dev_factor", 0.35) * max(b.activity, 0.25)
            if a_dev > threshold:
                add("Activity_change", act - b.activity,
                    min(dev.get("activity_cap", 6.0), (a_dev - threshold) * dev.get("activity_weight", 4.0)))

        sleep_attr = (f.sleep_deviation * 100.0) + f.sleep_irregularity
        if sleep_attr > 0:
            add("Sleep_variation", round(sleep_attr, 2),
                min(dev.get("sleep_cap", 10.0), sleep_attr * dev.get("sleep_weight", 0.8)))

        if f.stress_score > 0:
            add("Stress_level", f.stress_score,
                min(dev.get("stress_cap", 8.0), f.stress_score * dev.get("stress_weight", 0.6)))

        if f.trigger_load > 0:
            add("Trigger_exposure", f.trigger_load,
                min(dev.get("trigger_cap", 6.0), f.trigger_load * dev.get("trigger_weight", 0.9)))

        score = max(2.0, min(98.0, score))
        results = sorted(contributions, key=lambda c: c.contribution, reverse=True)
        return RiskResult(risk_score=round(score, 1),
                          risk_level=risk_level(score, self.band_low, self.band_high),
                          contributions=results)


def demo_signal_for_scenario(scenario: str) -> dict:
    """Signal preset for the simulation.

    Uses the calibrated ``demo_presets`` (derived from the real dataset) when
    available; falls back to the built-in scenario vectors otherwise.
    """
    try:
        cfg, calibrated = _load_config()
    except (OSError, ValueError):  # noqa: BLE001
        cfg, calibrated = DEFAULT_CONFIG, False

    if calibrated:
        preset = cfg.get("demo_presets", {}).get(scenario)
        if preset:
            signal = dict(preset)
            signal.setdefault("signal_quality", SIGNAL_QUALITY_BY_SCENARIO.get(scenario, 0.95))
            return signal

    if scenario == "normal":
        return {"heart_rate": 70, "hrv": 50, "systolic_bp": 118, "diastolic_bp": 76,
                "spo2": 98, "temperature": 36.5, "activity": 0.55, "signal_quality": 0.98}
    if scenario == "moderate":
        return {"heart_rate": 82, "hrv": 38, "systolic_bp": 126, "diastolic_bp": 82,
                "spo2": 98, "temperature": 36.7, "activity": 0.3, "signal_quality": 0.95}
    if scenario == "high":
        return {"heart_rate": 92, "hrv": 26, "systolic_bp": 138, "diastolic_bp": 88,
                "spo2": 97, "temperature": 36.9, "activity": 0.15, "signal_quality": 0.92}
    return demo_signal_for_scenario("normal")


def interpolate_signals(start: dict, end: dict, steps: int, jitter: float = 0.6) -> list[dict]:
    keys = ["heart_rate", "hrv", "systolic_bp", "diastolic_bp", "spo2", "temperature", "activity"]
    stream: list[dict] = []
    for i in range(steps):
        t = i / max(steps - 1, 1)
        point: dict = {"signal_quality": 0.94}
        for key in keys:
            s = start.get(key)
            e = end.get(key)
            if s is None or e is None:
                point[key] = None
                continue
            noise = (e - s) * 0.12 * jitter * (0.5 - (i / max(steps, 1) * 0.0 - 0.25))
            val = s + (e - s) * t + noise
            if key == "spo2":
                val = round(val)
            elif key == "temperature":
                val = round(val, 1)
            else:
                val = round(val, 1)
            point[key] = val
        stream.append(point)
    return stream