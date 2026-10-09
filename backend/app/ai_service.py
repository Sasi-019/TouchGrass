import json
import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


# ============================================================
# GROQ CONFIGURATION
# ============================================================

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

client = Groq(api_key=GROQ_API_KEY)


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
            raise RuntimeError(
                "Groq returned invalid JSON."
            )

        try:
            parsed = json.loads(
                text[start : end + 1]
            )

        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Groq returned invalid JSON: {exc}"
            )

    if not isinstance(parsed, dict):
        raise RuntimeError(
            "Groq JSON response was not an object."
        )

    return parsed


# ============================================================
# GENERIC GROQ CHAT
# ============================================================


def _chat_completion(
    system_prompt: str,
    user_prompt: str,
    max_completion_tokens: int = 1200,
    temperature: float = 0.2,
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

    if isinstance(content, str) and content.strip():
        return content.strip()

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

    transcription = client.audio.transcriptions.create(
        file=(
            filename,
            audio_bytes,
        ),
        model=GROQ_STT_MODEL,
        response_format="json",
        temperature=0.0,
    )

    text = getattr(
        transcription,
        "text",
        None,
    )

    if not text:
        raise RuntimeError(
            "Speech-to-text returned empty text."
        )

    return text.strip()