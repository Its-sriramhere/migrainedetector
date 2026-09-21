from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..api.deps import get_current_user
from ..db.session import get_db
from ..models import MigraineEpisode, User
from ..schemas import MigraineIn, MigraineOut

router = APIRouter(prefix="/api/migraine", tags=["migraine"])


@router.post("", response_model=MigraineOut, status_code=status.HTTP_201_CREATED)
def create_episode(
    body: MigraineIn,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    episode = MigraineEpisode(
        user_id=current.id,
        start_time=body.start_time,
        end_time=body.end_time,
        severity=body.severity,
        symptoms=body.symptoms,
        trigger=body.trigger,
        notes=body.notes,
    )
    db.add(episode)
    db.commit()
    db.refresh(episode)
    return episode


@router.get("/history", response_model=list[MigraineOut])
def history(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return (
        db.execute(
            select(MigraineEpisode)
            .where(MigraineEpisode.user_id == current.id)
            .order_by(MigraineEpisode.start_time.desc())
        )
        .scalars()
        .all()
    )


@router.put("/{episode_id}", response_model=MigraineOut)
def update_episode(
    episode_id: int,
    body: MigraineIn,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    episode = db.execute(
        select(MigraineEpisode).where(
            MigraineEpisode.id == episode_id,
            MigraineEpisode.user_id == current.id,
        )
    ).scalar_one_or_none()
    if episode is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Episode not found")
    episode.start_time = body.start_time
    episode.end_time = body.end_time
    episode.severity = body.severity
    episode.symptoms = body.symptoms
    episode.trigger = body.trigger
    episode.notes = body.notes
    db.commit()
    db.refresh(episode)
    return episode