import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..api.deps import get_current_user
from ..db.seed import build_risk_profile
from ..db.session import get_db
from ..models import AssessmentResponse, User, UserRiskProfile
from ..schemas import (
    AssessmentAnswerIn,
    AssessmentQuestionOut,
    AssessmentSubmitRequest,
    BaselineEstimates,
    RiskProfileOut,
)

router = APIRouter(prefix="/api/assessment", tags=["assessment"])


@router.get("/questions", response_model=list[AssessmentQuestionOut])
def get_questions(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT * FROM assessment_questions WHERE active = TRUE")).mappings().all()
    result = []
    for r in rows:
        d = dict(r)
        if isinstance(d.get("options"), str):
            d["options"] = json.loads(d["options"])
        result.append(AssessmentQuestionOut.model_validate(d))
    return result


@router.post("/responses", response_model=RiskProfileOut)
def submit_responses(
    body: AssessmentSubmitRequest,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    questions_rows = db.execute(text("SELECT * FROM assessment_questions")).mappings().all()
    questions = {r["id"]: r for r in questions_rows}
    if not questions:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Assessment not seeded")

    answers: dict[str, dict] = {}
    for item in body.answers:
        question = questions.get(item.question_id)
        if question is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown question {item.question_id}")
        answers[question["question_text"]] = {"answer": item.answer, "type": question["question_type"]}

    rows = []
    for item in body.answers:
        question = questions[item.question_id]
        rows.append((current.id, item.question_id, item.answer))

    if rows:
        db.execute(
            text("""INSERT INTO assessment_responses (user_id, question_id, answer)
                    VALUES (:uid, :qid, :ans)
                    ON CONFLICT (user_id, question_id) DO UPDATE SET answer = EXCLUDED.answer"""),
            [{"uid": uid, "qid": qid, "ans": ans} for uid, qid, ans in rows],
        )

    build_risk_profile(db, current.id, answers)

    profile = db.execute(
        text("SELECT * FROM user_risk_profiles WHERE user_id = :uid"),
        {"uid": current.id},
    ).mappings().first()
    d = dict(profile)
    if isinstance(d.get("trigger_profile"), str):
        d["trigger_profile"] = json.loads(d["trigger_profile"])
    return RiskProfileOut.model_validate(d)


@router.get("/profile", response_model=RiskProfileOut)
def get_profile(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    profile = db.execute(
        text("SELECT * FROM user_risk_profiles WHERE user_id = :uid"),
        {"uid": current.id},
    ).mappings().first()
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Profile not created yet")
    d = dict(profile)
    if isinstance(d.get("trigger_profile"), str):
        d["trigger_profile"] = json.loads(d["trigger_profile"])
    return RiskProfileOut.model_validate(d)


@router.get("/baseline", response_model=BaselineEstimates)
def get_baseline(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    from ..services.baseline_service import baseline_for

    profile = db.execute(
        text("SELECT * FROM user_risk_profiles WHERE user_id = :uid"),
        {"uid": current.id},
    ).mappings().first()
    d = dict(profile)
    if isinstance(d.get("trigger_profile"), str):
        d["trigger_profile"] = json.loads(d["trigger_profile"])
    baseline = baseline_for(db, current.id, d)
    return BaselineEstimates(
        heart_rate_low=round(baseline.heart_rate - 4, 1),
        heart_rate_high=round(baseline.heart_rate + 4, 1),
        sleep_hours=getattr(profile, "sleep_hours", None) if profile else None,
        resting_note="Learned from your physiological readings.",
    )