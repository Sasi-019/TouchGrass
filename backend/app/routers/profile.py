<<<<<<< HEAD
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

=======
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..ai_service import clean_profile, normalize_profile
from ..auth import verify_access_token
from ..database import get_db
from ..models import User, UserProfile
from ..schemas import ProfileCreate, ProfileResponse

>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
router = APIRouter(
    prefix="/profile",
    tags=["Profile"],
)

<<<<<<< HEAD
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

@router.post("/normalize")
def normalize_user_profile(
    payload: dict[str, Any],
    user_id: int = Depends(get_current_user_id),
) -> dict[str, Any]:
<<<<<<< HEAD
    """
    Turn the user's free-text discovery answers into a structured profile.

    The result is returned for the client to review/save with POST /profile.
    (Answers are deliberately NOT written to the server log: they are personal.)
    """

    answers = payload.get("answers")

    if not isinstance(answers, dict) or not answers:
=======

    answers = payload.get("answers")

    if not isinstance(answers, dict):
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
        raise HTTPException(
            status_code=400,
            detail="Request must contain an 'answers' object.",
        )

    try:
<<<<<<< HEAD
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
=======
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
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191


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
<<<<<<< HEAD
=======
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

>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
    profile = (
        db.query(UserProfile)
        .filter(UserProfile.user_id == user_id)
        .first()
    )

    if profile is None:
<<<<<<< HEAD
        profile = UserProfile(user_id=user_id)
=======
        profile = UserProfile(
            user_id=user_id,
        )
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
        db.add(profile)

    profile.interests = profile_data.interests
    profile.wants_more_of = profile_data.wants_more_of
    profile.curiosity = profile_data.curiosity
    profile.experience_preferences = (
        profile_data.experience_preferences
    )
    profile.dislikes = profile_data.dislikes
    profile.constraints = profile_data.constraints
<<<<<<< HEAD
    profile.typical_free_time = profile_data.typical_free_time
    profile.adventure_level = profile_data.adventure_level

    # learned_notes (feedback memory) is intentionally left untouched here,
    # so editing the profile never erases what TouchGrass has learned.
=======
    profile.typical_free_time = (
        profile_data.typical_free_time
    )
    profile.adventure_level = (
        profile_data.adventure_level
    )
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191

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
<<<<<<< HEAD
    }
=======
    }
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
