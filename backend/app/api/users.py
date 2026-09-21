from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..api.deps import get_current_user
from ..db.session import get_db
from ..models import User, UserProfile
from ..schemas import UserOut

router = APIRouter(prefix="/api/users", tags=["users"])

from pydantic import BaseModel, Field


class UserUpdateRequest(BaseModel):
    name: str = Field(default="", max_length=120)


@router.get("/me", response_model=UserOut)
def get_me(current: User = Depends(get_current_user)):
    return current


@router.put("/me", response_model=UserOut)
def update_me(body: UserUpdateRequest, current: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    if body.name:
        current.name = body.name
    db.commit()
    db.refresh(current)
    return current


@router.get("/me/profile", response_model=None)
def my_profile(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(UserProfile).filter(UserProfile.user_id == current.id).first()