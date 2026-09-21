from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..api.deps import get_current_user
from ..db.session import get_db
from ..models import Prediction, User
from ..ml.heuristic_engine import HeuristicEngine
from ..schemas import PredictRequest, PredictResponse, PredictionOut
from ..services.baseline_service import baseline_for, risk_factors_from_profile
from ..services.prediction_service import get_predictions
from ..models import UserRiskProfile

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


@router.get("/current", response_model=PredictionOut)
def current_prediction(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    prediction = (
        db.execute(
            select(Prediction)
            .where(Prediction.user_id == current.id)
            .order_by(Prediction.timestamp.desc())
            .limit(1)
            .options(joinedload(Prediction.features))
        )
        .scalars()
        .first()
    )
    if prediction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No prediction yet")
    return prediction


@router.get("/history", response_model=list[PredictionOut])
def prediction_history(limit: int = 50, db: Session = Depends(get_db),
                       current: User = Depends(get_current_user)):
    return get_predictions(db, current.id, limit)


@router.get("/{prediction_id}/explanation")
def prediction_explanation(prediction_id: int, db: Session = Depends(get_db),
                           current: User = Depends(get_current_user)):
    prediction = (
        db.execute(
            select(Prediction)
            .where(Prediction.id == prediction_id, Prediction.user_id == current.id)
            .options(joinedload(Prediction.features))
        )
        .scalars()
        .first()
    )
    if prediction is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Prediction not found")
    return {
        "prediction_id": prediction.id,
        "risk_score": prediction.risk_score,
        "risk_level": prediction.risk_level,
        "features": [
            {
                "name": f.feature_name,
                "value": f.feature_value,
                "contribution": f.contribution,
            }
            for f in prediction.features
        ],
    }


@router.post("/predict", response_model=PredictResponse)
def predict(body: PredictRequest, db: Session = Depends(get_db),
            current: User = Depends(get_current_user)):
    profile = db.execute(
        select(UserRiskProfile).where(UserRiskProfile.user_id == current.id)
    ).scalar_one_or_none()
    baseline = baseline_for(db, current.id, profile)
    factors = risk_factors_from_profile(profile)
    engine = HeuristicEngine()
    result = engine.evaluate(body.model_dump(), baseline, factors)
    return PredictResponse(
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        prediction_window_minutes=60,
        model_version=engine.model_version,
        explanation=[
            {"feature_name": c.feature_name, "feature_value": c.feature_value,
             "contribution": c.contribution}
            for c in result.contributions
        ],
    )