from sqlalchemy import select, text

from ..models import AssessmentQuestion
from ..db.session import Base, SessionLocal, engine

QUESTIONS: list[dict] = [
    {
        "question_text": "Have you experienced migraine or headache episodes before?",
        "question_type": "single",
        "options": ["Never", "Occasionally", "Frequently", "Very frequently"],
    },
    {
        "question_text": "How often do you typically experience migraine or headache episodes?",
        "question_type": "single",
        "options": ["Less than once/month", "1–3/month", "4–8/month", "More than 8/month"],
    },
    {
        "question_text": "How long does a typical episode last?",
        "question_type": "single",
        "options": ["Less than 2 hours", "2–6 hours", "6–12 hours", "More than 12 hours"],
    },
    {
        "question_text": "What symptoms usually occur with your episodes?",
        "question_type": "multi",
        "options": [
            "Head pain", "Nausea", "Light sensitivity", "Sound sensitivity",
            "Visual disturbances", "Dizziness", "Other",
        ],
    },
    {
        "question_text": "How many hours do you normally sleep?",
        "question_type": "single",
        "options": ["Less than 5", "5–6", "6–7", "7–8", "More than 8"],
    },
    {
        "question_text": "How consistent is your sleep schedule?",
        "question_type": "single",
        "options": ["Very consistent", "Mostly consistent", "Sometimes irregular", "Very irregular"],
    },
    {
        "question_text": "How physically active are you?",
        "question_type": "single",
        "options": ["Very low", "Low", "Moderate", "High"],
    },
    {
        "question_text": "How much caffeine do you normally consume?",
        "question_type": "single",
        "options": ["None", "1 serving/day", "2–3 servings/day", "More than 3 servings/day"],
    },
    {
        "question_text": "How would you describe your normal hydration?",
        "question_type": "single",
        "options": ["Low", "Moderate", "Good", "Very good"],
    },
    {
        "question_text": "How frequently do you experience significant stress?",
        "question_type": "single",
        "options": ["Rarely", "Occasionally", "Frequently", "Almost daily"],
    },
    {
        "question_text": "Which factors have you noticed may be associated with your headaches?",
        "question_type": "multi",
        "options": [
            "Lack of sleep", "Stress", "Skipping meals", "Dehydration", "Bright light",
            "Noise", "Caffeine changes", "Physical exertion", "Weather/environmental changes",
            "Other", "Not sure",
        ],
    },
    {
        "question_text": "What is your usual resting heart-rate range, if known?",
        "question_type": "single",
        "options": ["Less than 60", "60–70", "70–80", "80–90", "More than 90", "Don't know"],
    },
    {
        "question_text": "Do you regularly monitor your blood pressure?",
        "question_type": "single",
        "options": ["Yes", "No"],
    },
    {
        "question_text": "Have you noticed a consistent pattern before your headaches begin?",
        "question_type": "single",
        "options": ["Yes", "Sometimes", "No", "Not sure"],
    },
]

FREQUENCY_SCORES = {"Never": 0, "Occasionally": 2, "Frequently": 4, "Very frequently": 6}
HOW_OFTEN_SCORES = {
    "Less than once/month": 0, "1–3/month": 2, "4–8/month": 4, "More than 8/month": 6,
}
SLEEP_HOURS_VALUES = {
    "Less than 5": 4.5, "5–6": 5.5, "6–7": 6.5, "7–8": 7.5, "More than 8": 8.5,
}
RESTING_HR_VALUES = {
    "Less than 60": 57, "60–70": 65, "70–80": 75, "80–90": 85,
    "More than 90": 95, "Don't know": 72,
}
Q5_HOURS = {"Less than 5": 0, "5–6": 1, "6–7": 2, "7–8": 3, "More than 8": 4}
ACTIVITY_SCORES = {"Very low": 2, "Low": 1, "Moderate": 0, "High": 1}
CAFFEINE_SCORES = {"None": 0, "1 serving/day": 0, "2–3 servings/day": 2, "More than 3 servings/day": 3}
HYDRATION_SCORES = {"Low": 2, "Moderate": 1, "Good": 0, "Very good": 0}


def init_db() -> None:
    from .. import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def seed_questions(db) -> None:
    count = db.execute(select(AssessmentQuestion).limit(1)).scalar_one_or_none()
    if count is not None:
        return
    for q in QUESTIONS:
        db.add(AssessmentQuestion(
            question_text=q["question_text"],
            question_type=q["question_type"],
            options=q["options"],
            active=True,
        ))
    db.commit()


def _as_list(answer: str) -> list[str]:
    return [a.strip() for a in answer.split(",") if a.strip()]


import json
from sqlalchemy import text


def build_risk_profile(db, user_id: int, answers: dict[str, dict]) -> None:
    """answers maps question_text -> {'answer': str, 'type': 'single'|'multi'}"""
    from ..models import UserRiskProfile

    profile = db.execute(
        text("SELECT * FROM user_risk_profiles WHERE user_id = :uid"),
        {"uid": user_id},
    ).mappings().first()
    if profile is None:
        db.execute(
            text("INSERT INTO user_risk_profiles (user_id) VALUES (:uid)"),
            {"uid": user_id},
        )
        profile = dict(db.execute(
            text("SELECT * FROM user_risk_profiles WHERE user_id = :uid"),
            {"uid": user_id},
        ).mappings().first())
    else:
        profile = dict(profile)

    def single(text: str) -> str | None:
        entry = answers.get(text)
        return entry["answer"].strip() if entry and entry.get("answer") else None

    def multi(text: str) -> list[str]:
        entry = answers.get(text)
        if not entry or not entry.get("answer"):
            return []
        return _as_list(entry["answer"])

    q1 = single("Have you experienced migraine or headache episodes before?")
    q2 = single("How often do you typically experience migraine or headache episodes?")

    profile["migraine_history_score"] = min(
        12.0,
        (FREQUENCY_SCORES.get(q1 or "", 0) + HOW_OFTEN_SCORES.get(q2 or "", 0)) * 0.9,
    )

    profile["sleep_profile"] = single("How consistent is your sleep schedule?")
    q5 = single("How many hours do you normally sleep?")
    profile["sleep_hours"] = SLEEP_HOURS_VALUES.get(q5 or "", None)

    profile["stress_profile"] = single("How frequently do you experience significant stress?")
    profile["activity_profile"] = single("How physically active are you?")
    profile["hydration_profile"] = single("How would you describe your normal hydration?")
    profile["caffeine_profile"] = single("How much caffeine do you normally consume?")

    q11 = single("Which factors have you noticed may be associated with your headaches?")
    triggers = multi(q11) if q11 else []
    triggers = [t for t in triggers if t != "Not sure"]
    profile["trigger_profile"] = json.dumps(triggers or [])

    q12 = single("What is your usual resting heart-rate range, if known?")
    profile["resting_hr"] = RESTING_HR_VALUES.get(q12 or "", None)

    db.execute(
        text("""UPDATE user_risk_profiles 
                SET migraine_history_score = :mhs, sleep_profile = :sp, sleep_hours = :sh, 
                    stress_profile = :stp, activity_profile = :ap, hydration_profile = :hp, 
                    caffeine_profile = :cp, trigger_profile = :tp, resting_hr = :rh 
                WHERE user_id = :uid"""),
        {"mhs": profile["migraine_history_score"], "sp": profile["sleep_profile"], "sh": profile["sleep_hours"], "stp": profile["stress_profile"], "ap": profile["activity_profile"], "hp": profile["hydration_profile"], "cp": profile["caffeine_profile"], "tp": profile["trigger_profile"], "rh": profile["resting_hr"], "uid": user_id},
    )
    db.commit()


def run() -> None:
    init_db()
    db = SessionLocal()
    try:
        seed_questions(db)
        print("Database initialized and assessment questions seeded.")
    finally:
        db.close()


if __name__ == "__main__":
    run()