import logging

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)

from ..ai_service import AIServiceError, transcribe_audio
from ..auth import get_current_user_id
from ..config import get_settings
from ..schemas import VoiceTranscriptionResponse

logger = logging.getLogger("touchgrass.voice")

router = APIRouter(
    prefix="/voice",
    tags=["Voice"],
)

ALLOWED_EXTENSIONS = (
    ".webm", ".wav", ".mp3", ".m4a", ".ogg", ".mp4", ".mpeg", ".mpga", ".flac",
)


@router.post(
    "/transcribe",
    response_model=VoiceTranscriptionResponse,
)
async def transcribe_voice(
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

    if not audio_bytes:
        raise HTTPException(
            status_code=400,
            detail="The recording was empty.",
        )

    if len(audio_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail="The recording is too long. Please keep it shorter.",
        )

    try:
        text = transcribe_audio(
            audio_bytes=audio_bytes,
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
