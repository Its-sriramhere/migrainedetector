"""Explainable-advice engine.

Deterministic, rule-based "what to do now" guidance. It maps the physiological
features that deviated (the engine's contributions) to concrete calming steps,
and always ends with universal low-effort actions. No LLM, no cost, fully
explainable: each tip can be traced back to the signal that triggered it.
"""
from typing import Any, Sequence

MAX_STEPS = 4

TIP_BY_FEATURE: dict[str, str] = {
    "HR_increase": (
        "Rest and breathe slowly — in for 4 seconds, out for 6 "
        "— to settle your heart rate."
    ),
    "HRV_decrease": (
        "Step away from screens and try slow breathing to help your "
        "heart rate variability recover."
    ),
    "BP_variation": (
        "Unclench your jaw and neck, breathe out longer than you breathe in, "
        "and sit quietly for a few minutes."
    ),
    "SpO2_drop": (
        "Move to fresh air, sit upright and breathe slowly to restore "
        "normal oxygen levels."
    ),
    "Temperature_change": (
        "Cool the room if you feel warm, remove a layer, and drink "
        "a glass of water."
    ),
    "Activity_change": "Pause physical activity and sit or lie down for a few minutes.",
    "Sleep_variation": "Protect your next sleep — a regular sleep schedule lowers risk.",
    "Stress_level": "Step away from the source of stress and do a short calming activity.",
    "Trigger_exposure": "If you can identify the trigger, move away from it for a while.",
}

UNIVERSAL_TIPS: list[str] = [
    "Drink a glass of water.",
    "Take a 5-minute break away from your desk.",
    "Dim the lights and reduce noise.",
]


def _contribution(item: Any) -> float:
    return getattr(item, "contribution", 0) or 0


def _feature_name(item: Any) -> str:
    return getattr(item, "feature_name", "") or ""


def build_advice(risk_level: str, contributions: Sequence[Any]) -> list[dict[str, Any]]:
    """Return up to MAX_STEPS ordered {step, guidance} steps, or [] for low risk."""
    if risk_level not in ("high", "moderate"):
        return []

    ranked = sorted(
        (c for c in contributions if _contribution(c) > 0),
        key=_contribution,
        reverse=True,
    )
    selected: list[str] = []
    for item in ranked:
        tip = TIP_BY_FEATURE.get(_feature_name(item))
        if tip and tip not in selected:
            selected.append(tip)
    for tip in UNIVERSAL_TIPS:
        if tip not in selected:
            selected.append(tip)

    return [
        {"step": i + 1, "guidance": text}
        for i, text in enumerate(selected[:MAX_STEPS])
    ]


def advice_lines(advice: Sequence[dict[str, Any]]) -> list[str]:
    return [item["guidance"] for item in advice]