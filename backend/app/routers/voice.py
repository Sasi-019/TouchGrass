from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from ..ai_service import transcribe_audio
from ..auth import verify_access_token
from ..schemas import VoiceTranscriptionResponse


router = APIRouter(
    prefix="/voice",
    tags=["Voice"],
)

security = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
) -> int:

    user_id = verify_access_token(
        credentials.credentials
    )

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )

    return user_id


@router.post(
    "/transcribe",
    response_model=VoiceTranscriptionResponse,
)
async def transcribe_voice(
    file: UploadFile = File(...),
    user_id: int = Depends(
        get_current_user_id
    ),
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Audio filename is missing.",
        )

    allowed_extensions = {
        ".webm",
        ".wav",
        ".mp3",
        ".m4a",
        ".ogg",
        ".mp4",
    }

    filename = file.filename.lower()

    if not any(
        filename.endswith(extension)
        for extension in allowed_extensions
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported audio format. "
                "Use webm, wav, mp3, m4a, ogg, or mp4."
            ),
        )

    audio_bytes = await file.read()

    if not audio_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded audio is empty.",
        )

    if len(audio_bytes) > 25 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Audio file is too large.",
        )

    try:
        text = transcribe_audio(
            audio_bytes=audio_bytes,
            filename=file.filename,
        )

        return VoiceTranscriptionResponse(
            text=text,
            model="whisper-large-v3-turbo",
        )

    except Exception as exc:
        print(
            "\n========== SPEECH TO TEXT ERROR =========="
        )
        print(type(exc).__name__)
        print(str(exc))
        print(
            "==========================================\n"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Speech-to-text failed: "
                f"{type(exc).__name__}: {str(exc)}"
            ),
        )