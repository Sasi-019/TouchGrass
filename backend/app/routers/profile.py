import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..ai_service import AIServiceError, clean_profile, normalize_profile
from ..auth import get_current_user_id
from ..database import get_db
from ..models import UserProfile
from ..schemas import ProfileCreate, ProfileResponse

logger = logging.getLogger("touchgrass.profile")

router = APIRouter(
    prefix="/profile",
    tags=["Profile"],
)


@router.post("/normalize")
def normalize_user_profile(
    payload: dict[str, Any],
    user_id: int = Depends(get_current_user_id),
) -> dict[str, Any]:
    """
    Turn the user's free-text discovery answers into a structured profile.

    The result is returned for the client to review/save with POST /profile.
    (Answers are deliberately NOT written to the server log: they are personal.)
    """

    answers = payload.get("answers")

    if not isinstance(answers, dict) or not answers:
        raise HTTPException(
            status_code=400,
            detail="Request must contain an 'answers' object.",
        )

    try:
        return clean_profile(normalize_profile(answers))

    except AIServiceError as exc:
        logger.warning("Profile AI failed: %s", exc)

        raise HTTPException(
            status_code=502,
            detail=(
                "The AI assistant couldn't understand your answers just now. "
                "Please try again in a moment."
            ),
        ) from exc


@router.get(
    "",
    response_model=ProfileResponse,
)
def get_profile(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(UserProfile)
        .filter(UserProfile.user_id == user_id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found.",
        )

    return profile


@router.post(
    "",
    response_model=ProfileResponse,
)
def create_or_update_profile(
    profile_data: ProfileCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(UserProfile)
        .filter(UserProfile.user_id == user_id)
        .first()
    )

    if profile is None:
        profile = UserProfile(user_id=user_id)
        db.add(profile)

    profile.interests = profile_data.interests
    profile.wants_more_of = profile_data.wants_more_of
    profile.curiosity = profile_data.curiosity
    profile.experience_preferences = (
        profile_data.experience_preferences
    )
    profile.dislikes = profile_data.dislikes
    profile.constraints = profile_data.constraints
    profile.typical_free_time = profile_data.typical_free_time
    profile.adventure_level = profile_data.adventure_level

    # learned_notes (feedback memory) is intentionally left untouched here,
    # so editing the profile never erases what TouchGrass has learned.

    db.commit()
    db.refresh(profile)

    return profile


@router.delete("")
def delete_profile(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(UserProfile)
        .filter(UserProfile.user_id == user_id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found.",
        )

    db.delete(profile)
    db.commit()

    return {
        "message": "Profile deleted successfully."
    }
