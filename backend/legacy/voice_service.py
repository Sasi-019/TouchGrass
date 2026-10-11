import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set")


client = Groq(api_key=GROQ_API_KEY)


WHISPER_MODEL = os.getenv(
    "WHISPER_MODEL",
    "whisper-large-v3-turbo",
)


def transcribe_audio(
    audio_file,
    filename: str,
) -> str:

    result = client.audio.transcriptions.create(
        file=(
            filename,
            audio_file,
        ),
        model=WHISPER_MODEL,
        response_format="json",
        temperature=0,
    )

    return result.text.strip()