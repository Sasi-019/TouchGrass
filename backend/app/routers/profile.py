from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import UserProfile
from ..schemas import ProfileCreate, ProfileResponse
from ..auth import verify_access_token
from ..ai_service import normalize_profile


router = APIRouter(
    prefix="/profile",
    tags=["Profile"]
)

security = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    user_id = verify_access_token(
        credentials.credentials
    )

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    return user_id


@router.post(
    "",
    response_model=ProfileResponse
)
def create_or_update_profile(
    profile_data: ProfileCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):

    profile = (
        db.query(UserProfile)
        .filter(UserProfile.user_id == user_id)
        .first()
    )

    if profile is None:

        profile = UserProfile(
            user_id=user_id
        )

        db.add(profile)

    profile.interests = profile_data.interests

    profile.wants_more_of = (
        profile_data.wants_more_of
    )

    profile.curiosity = (
        profile_data.curiosity
    )

    profile.experience_preferences = (
        profile_data.experience_preferences
    )

    profile.dislikes = (
        profile_data.dislikes
    )

    profile.constraints = (
        profile_data.constraints
    )

    profile.typical_free_time = (
        profile_data.typical_free_time
    )

    db.commit()
    db.refresh(profile)

    return profile


@router.get(
    "",
    response_model=ProfileResponse
)
def get_profile(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):

    profile = (
        db.query(UserProfile)
        .filter(UserProfile.user_id == user_id)
        .first()
    )

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )

    return profile


@router.post("/normalize")
def normalize_user_profile(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(UserProfile)
        .filter(UserProfile.user_id == user_id)
        .first()
    )

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Profile not found",
        )

    raw_profile = {
        "interests": profile.interests or [],
        "wants_more_of": profile.wants_more_of or [],
        "curiosity": profile.curiosity or [],
        "experience_preferences":
            profile.experience_preferences or [],
        "dislikes": profile.dislikes or [],
        "constraints": profile.constraints or [],
        "typical_free_time":
            profile.typical_free_time or "",
    }

    try:
        normalized = normalize_profile(raw_profile)
    except Exception as exc:
        print("AI profile normalization failed:", exc)

        raise HTTPException(
            status_code=502,
            detail="AI profile analysis failed",
        )

    profile.interests = normalized.get(
        "interests",
        [],
    )

    profile.wants_more_of = normalized.get(
        "wants_more_of",
        [],
    )

    profile.curiosity = normalized.get(
        "curiosity",
        [],
    )

    profile.experience_preferences = normalized.get(
        "experience_preferences",
        [],
    )

    profile.dislikes = normalized.get(
        "dislikes",
        [],
    )

    profile.constraints = normalized.get(
        "constraints",
        [],
    )

    profile.typical_free_time = normalized.get(
        "typical_free_time",
        "",
    )

    db.commit()
    db.refresh(profile)

    return {
        "message": "Profile normalized successfully",
        "profile": profile,
    }