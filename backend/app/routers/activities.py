<<<<<<< HEAD
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user_id
from ..database import get_db
from ..memory_service import apply_feedback_to_profile
=======

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..auth import verify_access_token
from ..database import get_db
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
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

<<<<<<< HEAD

def _normalize_completed(value: str | None) -> str | None:
    """Store a small, consistent vocabulary: completed / skipped."""

    if value is None:
        return None

    value = value.strip().lower()

    if value in {"yes", "y", "true", "done", "completed", "complete"}:
        return "completed"

    if value in {"no", "n", "false", "skipped", "not_done", "didnt", "skip"}:
        return "skipped"

    return value[:30] or None
=======
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
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191


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
<<<<<<< HEAD
    """Activity history, newest first."""

    return (
        db.query(Activity)
        .filter(Activity.user_id == user_id)
        .order_by(Activity.created_at.desc(), Activity.id.desc())
        .all()
    )

=======
    activities = (
        db.query(Activity)
        .filter(Activity.user_id == user_id)
        .order_by(Activity.created_at.desc())
        .all()
    )

    return activities

>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191

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
<<<<<<< HEAD
    # Users can only give feedback on their own activities.
=======
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
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

<<<<<<< HEAD
    completed = _normalize_completed(feedback_data.completed)

=======
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
    feedback = ActivityFeedback(
        activity_id=activity_id,
        user_id=user_id,
        rating=feedback_data.rating,
<<<<<<< HEAD
        completed=completed,
        comment=feedback_data.comment,
    )

    if completed:
        activity.status = completed
=======
        completed=feedback_data.completed,
        comment=feedback_data.comment,
    )

    if feedback_data.completed:
        activity.status = feedback_data.completed
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

<<<<<<< HEAD
    # Learn from it. Best effort: feedback is already saved above, and this
    # call never raises.
    note = apply_feedback_to_profile(
        db=db,
        user_id=user_id,
        activity=activity,
        rating=feedback_data.rating,
        comment=feedback_data.comment,
        completed=completed,
    )

    return FeedbackResponse(
        id=feedback.id,
        activity_id=feedback.activity_id,
        user_id=feedback.user_id,
        rating=feedback.rating,
        completed=feedback.completed,
        comment=feedback.comment,
        memory_note=note,
    )
=======
    return feedback
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
