import json
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set")

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b",
)

client = Groq(api_key=GROQ_API_KEY)


SYSTEM_PROMPT = """
You are the profile-understanding component of TouchGrass.

TouchGrass is a real-world activity agent that helps users spend
less passive screen time and do meaningful offline activities.

Your task is to convert a user's natural-language profile answers
into a structured JSON profile.

Important rules:

1. Extract genuine interests from the user's answers.
2. Do not invent interests that the user did not imply.
3. Give each interest a strength from 0.0 to 1.0.
4. Identify things the user wants to do more often.
5. Identify things the user is curious about.
6. Preserve their preferred experience types.
7. Preserve dislikes and constraints.
8. Preserve their typical available time.
9. Keep the result concise.
10. Return ONLY valid JSON.
11. Do not include markdown.
12. Do not include explanations outside the JSON.

Required JSON format:

{
  "interests": [
    {
      "name": "string",
      "strength": 0.0
    }
  ],
  "wants_more_of": [],
  "curiosity": [],
  "experience_preferences": [],
  "dislikes": [],
  "constraints": [],
  "typical_free_time": "string"
}
"""


def normalize_profile(raw_profile: dict) -> dict:

    user_prompt = f"""
Convert this user's answers into the required TouchGrass profile.

USER ANSWERS:

Interests:
{raw_profile.get("interests", [])}

Wants more of:
{raw_profile.get("wants_more_of", [])}

Curiosity:
{raw_profile.get("curiosity", [])}

Experience preferences:
{raw_profile.get("experience_preferences", [])}

Dislikes:
{raw_profile.get("dislikes", [])}

Constraints:
{raw_profile.get("constraints", [])}

Typical free time:
{raw_profile.get("typical_free_time", "")}
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0.2,
        max_tokens=600,
        response_format={
            "type": "json_object"
        },
    )

    content = response.choices[0].message.content.strip()

    try:
        profile = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Groq returned invalid JSON: {content}"
        ) from exc

    return profile