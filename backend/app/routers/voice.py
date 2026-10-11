<<<<<<< HEAD
import logging

=======
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
<<<<<<< HEAD

from ..ai_service import AIServiceError, transcribe_audio
from ..auth import get_current_user_id
from ..config import get_settings
from ..schemas import VoiceTranscriptionResponse

logger = logging.getLogger("touchgrass.voice")
=======
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from ..ai_service import transcribe_audio
from ..auth import verify_access_token
from ..schemas import VoiceTranscriptionResponse

>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191

router = APIRouter(
    prefix="/voice",
    tags=["Voice"],
)

<<<<<<< HEAD
ALLOWED_EXTENSIONS = (
    ".webm", ".wav", ".mp3", ".m4a", ".ogg", ".mp4", ".mpeg", ".mpga", ".flac",
)
=======
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
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191


@router.post(
    "/transcribe",
    response_model=VoiceTranscriptionResponse,
)
async def transcribe_voice(
<<<<<<< HEAD
    # The browser field is called "file". "audio" is accepted too, because the
    # original frontend sent that name, so older clients keep working.
    file: UploadFile | None = File(default=None),
    audio: UploadFile | None = File(default=None),
    user_id: int = Depends(get_current_user_id),
):
    upload = file or audio

    if upload is None:
        raise HTTPException(
            status_code=400,
            detail="No audio was uploaded (expected a 'file' field).",
        )

    filename = (upload.filename or "voice.webm").lower()

    # Browsers sometimes send names like "blob" with no extension.
    # Fall back to the declared content type.
    if not filename.endswith(ALLOWED_EXTENSIONS):
        content_type = (upload.content_type or "").lower()

        if "webm" in content_type:
            filename = "voice.webm"
        elif "ogg" in content_type:
            filename = "voice.ogg"
        elif "mp4" in content_type or "m4a" in content_type or "aac" in content_type:
            filename = "voice.m4a"
        elif "wav" in content_type:
            filename = "voice.wav"
        elif "mpeg" in content_type or "mp3" in content_type:
            filename = "voice.mp3"
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported audio format. Please type your request instead.",
            )

    max_bytes = get_settings().max_audio_mb * 1024 * 1024

    # Read one byte past the limit so oversized uploads are detected
    # without loading an unbounded file into memory.
    audio_bytes = await upload.read(max_bytes + 1)
=======
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
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191

    if not audio_bytes:
        raise HTTPException(
            status_code=400,
<<<<<<< HEAD
            detail="The recording was empty.",
        )

    if len(audio_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail="The recording is too long. Please keep it shorter.",
=======
            detail="Uploaded audio is empty.",
        )

    if len(audio_bytes) > 25 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Audio file is too large.",
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
        )

    try:
        text = transcribe_audio(
            audio_bytes=audio_bytes,
<<<<<<< HEAD
            filename=filename,
        )

    except AIServiceError as exc:
        logger.warning("Speech-to-text failed: %s", exc)

        # 422 for "no speech", 502 for provider trouble; the message always
        # tells the user they can simply type instead.
        status = 422 if "No speech" in str(exc) else 502

        raise HTTPException(
            status_code=status,
            detail=(
                "I couldn't understand that recording. "
                "You can type your request instead."
            ),
        ) from exc

    return VoiceTranscriptionResponse(
        text=text,
        model=get_settings().whisper_model,
    )
=======
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
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
