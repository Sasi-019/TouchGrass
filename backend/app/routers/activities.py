
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..auth import verify_access_token
from ..database import get_db
from ..models import Activity, ActivityFeedback
from ..schemas import (
    ActivityCreate,
    ActivityResponse,
    FeedbackCreate,
    FeedbackResponse,
)

router = APIRouter(
    prefix="/activities",
    tags=["Activities"],
)

security = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    user_id = verify_access_token(credentials.credentials)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )

    return user_id


@router.post(
    "",
    response_model=ActivityResponse,
)
def create_activity(
    activity_data: ActivityCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    activity = Activity(
        user_id=user_id,
        title=activity_data.title,
        description=activity_data.description,
        category=activity_data.category,
        duration_minutes=activity_data.duration_minutes,
        context=activity_data.context,
        status="suggested",
    )

    db.add(activity)
    db.commit()
    db.refresh(activity)

    return activity


@router.get(
    "",
    response_model=list[ActivityResponse],
)
def get_activities(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    activities = (
        db.query(Activity)
        .filter(Activity.user_id == user_id)
        .order_by(Activity.created_at.desc())
        .all()
    )

    return activities


@router.get(
    "/{activity_id}",
    response_model=ActivityResponse,
)
def get_activity(
    activity_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    activity = (
        db.query(Activity)
        .filter(
            Activity.id == activity_id,
            Activity.user_id == user_id,
        )
        .first()
    )

    if not activity:
        raise HTTPException(
            status_code=404,
            detail="Activity not found.",
        )

    return activity


@router.post(
    "/{activity_id}/feedback",
    response_model=FeedbackResponse,
)
def submit_feedback(
    activity_id: int,
    feedback_data: FeedbackCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    activity = (
        db.query(Activity)
        .filter(
            Activity.id == activity_id,
            Activity.user_id == user_id,
        )
        .first()
    )

    if not activity:
        raise HTTPException(
            status_code=404,
            detail="Activity not found.",
        )

    feedback = ActivityFeedback(
        activity_id=activity_id,
        user_id=user_id,
        rating=feedback_data.rating,
        completed=feedback_data.completed,
        comment=feedback_data.comment,
    )

    if feedback_data.completed:
        activity.status = feedback_data.completed

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return feedback
