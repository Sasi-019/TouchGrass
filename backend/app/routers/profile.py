from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..ai_service import clean_profile, normalize_profile
from ..auth import verify_access_token
from ..database import get_db
from ..models import User, UserProfile
from ..schemas import ProfileCreate, ProfileResponse

router = APIRouter(
    prefix="/profile",
    tags=["Profile"],
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


@router.post("/normalize")
def normalize_user_profile(
    payload: dict[str, Any],
    user_id: int = Depends(get_current_user_id),
) -> dict[str, Any]:

    answers = payload.get("answers")

    if not isinstance(answers, dict):
        raise HTTPException(
            status_code=400,
            detail="Request must contain an 'answers' object.",
        )

    try:
        print("\n========== PROFILE NORMALIZATION ==========")
        print("User ID:", user_id)
        print("Answers:", answers)

        raw_profile = normalize_profile(answers)

        print("Raw Groq profile:")
        print(raw_profile)

        profile = clean_profile(raw_profile)

        print("Cleaned profile:")
        print(profile)
        print("===========================================\n")

        return profile

    except Exception as exc:
        print("\n========== PROFILE AI ERROR ==========")
        print(type(exc).__name__)
        print(str(exc))
        print("======================================\n")

        raise HTTPException(
            status_code=500,
            detail=f"Profile AI normalization failed: {type(exc).__name__}: {str(exc)}",
        )


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
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    profile = (
        db.query(UserProfile)
        .filter(UserProfile.user_id == user_id)
        .first()
    )

    if profile is None:
        profile = UserProfile(
            user_id=user_id,
        )
        db.add(profile)

    profile.interests = profile_data.interests
    profile.wants_more_of = profile_data.wants_more_of
    profile.curiosity = profile_data.curiosity
    profile.experience_preferences = (
        profile_data.experience_preferences
    )
    profile.dislikes = profile_data.dislikes
    profile.constraints = profile_data.constraints
    profile.typical_free_time = (
        profile_data.typical_free_time
    )
    profile.adventure_level = (
        profile_data.adventure_level
    )

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