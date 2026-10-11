import json
<<<<<<< HEAD
import logging
from typing import Any

from groq import Groq

from .config import require_valid_settings
from .prompts import PROFILE_SYSTEM_PROMPT

logger = logging.getLogger("touchgrass.ai")
=======
import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq

load_dotenv()
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191


# ============================================================
# GROQ CONFIGURATION
# ============================================================

<<<<<<< HEAD
settings = require_valid_settings()

GROQ_API_KEY = settings.groq_api_key
GROQ_MODEL = settings.groq_model
GROQ_STT_MODEL = settings.whisper_model
=======
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b",
)

GROQ_STT_MODEL = os.getenv(
    "GROQ_STT_MODEL",
    "whisper-large-v3-turbo",
)

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set in backend/.env"
    )
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191

client = Groq(api_key=GROQ_API_KEY)


<<<<<<< HEAD
class AIServiceError(RuntimeError):
    """The language model (or speech model) could not produce a usable result."""


# ============================================================
# PROFILE NORMALIZATION
#
# The prompt now lives in prompts.py together with the other agent prompts.
# ============================================================

=======
# ============================================================
# PROFILE NORMALIZATION
# ============================================================

PROFILE_SYSTEM_PROMPT = """
You are the profile-understanding engine for TouchGrass.

TouchGrass is an AI system that helps people discover meaningful
real-world activities based on their personality, interests,
available time, curiosity, preferences, and constraints.

The user answers conversational questions.

Your job is to transform those answers into a structured profile.

Return ONLY valid JSON.

The JSON must contain:

{
    "interests": [],
    "wants_more_of": [],
    "curiosity": [],
    "experience_preferences": [],
    "dislikes": [],
    "constraints": [],
    "typical_free_time": "",
    "adventure_level": ""
}

Rules:

1. interests:
   Extract meaningful interests from the user's answers.
   Examples:
   photography, music, nature, technology, food, art,
   fitness, reading, animals, history.

2. wants_more_of:
   Identify experiences the user wants more of.
   Examples:
   social connection, creativity, adventure, exercise,
   learning, relaxation, exploration.

3. curiosity:
   Extract subjects or experiences the user is curious about.

4. experience_preferences:
   Capture preferred activity styles.
   Examples:
   solo, friends, outdoors, indoors, creative, social,
   quiet, spontaneous, structured.

5. dislikes:
   Extract things the user explicitly dislikes.

6. constraints:
   Extract practical limitations.
   Examples:
   limited budget, limited time, transportation,
   crowds, weather sensitivity.

7. typical_free_time:
   Preserve the user's typical available time.

8. adventure_level:
   Classify as one of:
   "low", "moderate", "high"

Do not invent information that is not supported by the answers.

Keep the profile concise and useful for recommending
real-world activities.
"""

>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191

def extract_json(text: str) -> dict[str, Any]:
    """
    Extract a JSON object from an LLM response.
    """

    text = text.strip()

    # Remove markdown code fences if the model adds them.
    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    try:
        parsed = json.loads(text)

    except json.JSONDecodeError:

        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1 or end <= start:
<<<<<<< HEAD
            raise AIServiceError(
                "The AI model returned an unreadable answer."
=======
            raise RuntimeError(
                "Groq returned invalid JSON."
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
            )

        try:
            parsed = json.loads(
                text[start : end + 1]
            )

        except json.JSONDecodeError as exc:
<<<<<<< HEAD
            raise AIServiceError(
                "The AI model returned an unreadable answer."
            ) from exc

    if not isinstance(parsed, dict):
        raise AIServiceError(
            "The AI model returned an unexpected answer."
=======
            raise RuntimeError(
                f"Groq returned invalid JSON: {exc}"
            )

    if not isinstance(parsed, dict):
        raise RuntimeError(
            "Groq JSON response was not an object."
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
        )

    return parsed


# ============================================================
# GENERIC GROQ CHAT
# ============================================================


<<<<<<< HEAD
def _is_reasoning_model() -> bool:
    return "gpt-oss" in GROQ_MODEL.lower()


=======
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
def _chat_completion(
    system_prompt: str,
    user_prompt: str,
    max_completion_tokens: int = 1200,
    temperature: float = 0.2,
<<<<<<< HEAD
    json_mode: bool = False,
) -> str:
    request: dict[str, Any] = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
    }

    if _is_reasoning_model():
        # Reasoning tokens count against the completion budget. Keep the
        # reasoning short and leave generous room for the actual answer,
        # otherwise the visible reply can come back empty.
        # extra_body goes straight onto the request, so this works with
        # older groq SDK versions that don't know these arguments yet.
        request["extra_body"] = {
            "reasoning_effort": "low",
            "include_reasoning": False,
        }
        request["max_completion_tokens"] = max_completion_tokens + 1500
    else:
        request["max_completion_tokens"] = max_completion_tokens

    if json_mode:
        request["response_format"] = {"type": "json_object"}

    try:
        try:
            completion = client.chat.completions.create(**request)
        except Exception:
            if not json_mode:
                raise
            # Some models reject response_format. Retry once without it;
            # extract_json() copes with fenced or chatty output.
            request.pop("response_format", None)
            completion = client.chat.completions.create(**request)
    except Exception as exc:
        # Never include headers or the API key in the message.
        raise AIServiceError(
            f"Groq request failed: {type(exc).__name__}"
        ) from exc

    if not completion.choices:
        raise AIServiceError("Groq returned no choices.")

    choice = completion.choices[0]
    content = choice.message.content
=======
) -> str:
    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=temperature,
            max_completion_tokens=max_completion_tokens,
            include_reasoning=False,
        )
    except Exception as exc:
        # Do not print the API key or request headers.
        raise RuntimeError(
            f"Groq API request failed: {type(exc).__name__}: {exc}"
        ) from exc

    if not completion.choices:
        raise RuntimeError(
            f"Groq returned no choices. "
            f"Model: {GROQ_MODEL}; "
            f"finish_reason: {completion.choices}"
        )

    choice = completion.choices[0]
    message = choice.message
    content = message.content
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191

    if isinstance(content, str) and content.strip():
        return content.strip()

<<<<<<< HEAD
    logger.warning(
        "Empty model output. model=%s finish_reason=%s",
        GROQ_MODEL,
        getattr(choice, "finish_reason", None),
    )

    raise AIServiceError(
        "The AI model returned an empty answer. Please try again."
    )


=======
    # Report diagnostic metadata without logging prompts or secrets.
    reasoning = getattr(message, "reasoning", None)
    finish_reason = getattr(choice, "finish_reason", None)
    usage = getattr(completion, "usage", None)
    completion_tokens = getattr(
        usage, "completion_tokens", None
    )

    raise RuntimeError(
        "Groq returned no usable text. "
        f"Model: {GROQ_MODEL}; "
        f"finish_reason: {finish_reason}; "
        f"completion_tokens: {completion_tokens}; "
        f"reasoning_present: {bool(reasoning)}. "
        "Check the model response and token configuration."
    )

>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
def generate_json(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 800,
) -> dict[str, Any]:

    content = _chat_completion(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_completion_tokens=max_tokens,
        temperature=temperature,
<<<<<<< HEAD
        json_mode=True,
=======
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
    )

    return extract_json(content)


def generate_text(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 800,
) -> str:

    return _chat_completion(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_completion_tokens=max_tokens,
        temperature=temperature,
    )


# ============================================================
# PROFILE FUNCTIONS
# ============================================================

def normalize_profile(
    answers: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert raw conversational profile answers
    into structured profile data.
    """

    user_prompt = f"""
Here are the user's profile discovery answers:

{json.dumps(answers, ensure_ascii=False, indent=2)}

Convert these answers into the required structured
TouchGrass profile.

Return ONLY JSON.
"""

    profile = generate_json(
        system_prompt=PROFILE_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.2,
        max_tokens=700,
    )

    return clean_profile(profile)


def clean_profile(
    profile: dict[str, Any],
) -> dict[str, Any]:
    """
    Ensure the normalized profile has the expected
    structure and safe value types.
    """

    list_fields = [
        "wants_more_of",
        "curiosity",
        "experience_preferences",
        "dislikes",
        "constraints",
    ]

    for field in list_fields:

        value = profile.get(field)

        if value is None:
            profile[field] = []

        elif isinstance(value, str):
            profile[field] = [value]

        elif not isinstance(value, list):
            profile[field] = []

    interests = profile.get("interests")

    if interests is None:
        profile["interests"] = []

    elif not isinstance(interests, list):
        profile["interests"] = []

    profile["typical_free_time"] = (
        profile.get("typical_free_time")
        or ""
    )

    adventure_level = profile.get(
        "adventure_level"
    )

    if adventure_level not in {
        "low",
        "moderate",
        "high",
    }:

        profile["adventure_level"] = "moderate"

    return profile


# ============================================================
# SPEECH TO TEXT
# ============================================================

def transcribe_audio(
    audio_bytes: bytes,
    filename: str = "voice.webm",
) -> str:
    """
    Convert uploaded audio into text using
    Groq Whisper.
    """

    if not audio_bytes:
        raise ValueError(
            "Audio file is empty."
        )

<<<<<<< HEAD
    try:
        transcription = client.audio.transcriptions.create(
            file=(
                filename,
                audio_bytes,
            ),
            model=GROQ_STT_MODEL,
            response_format="json",
            temperature=0.0,
        )
    except Exception as exc:
        raise AIServiceError(
            f"Speech-to-text request failed: {type(exc).__name__}"
        ) from exc
=======
    transcription = client.audio.transcriptions.create(
        file=(
            filename,
            audio_bytes,
        ),
        model=GROQ_STT_MODEL,
        response_format="json",
        temperature=0.0,
    )
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191

    text = getattr(
        transcription,
        "text",
        None,
    )

<<<<<<< HEAD
    if not text or not text.strip():
        raise AIServiceError(
            "No speech was detected in the recording."
=======
    if not text:
        raise RuntimeError(
            "Speech-to-text returned empty text."
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
        )

    return text.strip()