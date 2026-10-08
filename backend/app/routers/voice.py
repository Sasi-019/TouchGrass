from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)

from ..auth import verify_access_token
from ..voice_service import transcribe_audio


router = APIRouter(
    prefix="/voice",
    tags=["Voice"],
)

security = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user_id = verify_access_token(
        credentials.credentials
    )

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    return user_id


@router.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
):

    if not audio.content_type:
        raise HTTPException(
            status_code=400,
            detail="Audio type is missing",
        )

    audio_bytes = await audio.read()

    if not audio_bytes:
        raise HTTPException(
            status_code=400,
            detail="Empty audio file",
        )

    try:
        text = transcribe_audio(
            audio_bytes,
            audio.filename or "recording.webm",
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {exc}",
        )

    return {
        "text": text,
    }