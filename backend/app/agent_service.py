import json
import os

from typing import TypedDict

from dotenv import load_dotenv
from groq import Groq

from langgraph.graph import StateGraph, START, END

from sqlalchemy.orm import Session

from .models import (
    UserProfile,
    Activity,
)


load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set")


GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b",
)


client = Groq(
    api_key=GROQ_API_KEY
)


class AgentState(TypedDict, total=False):

    user_id: int

    user_message: str

    latitude: float | None
    longitude: float | None

    profile: dict

    recent_activities: list

    intent: str

    place_query: str | None

    current_context: dict

    activity: dict

    activity_id: int

    response: str


def load_user_profile(
    state: AgentState,
    db: Session,
):

    profile = (
        db.query(UserProfile)
        .filter(
            UserProfile.user_id
            == state["user_id"]
        )
        .first()
    )

    if not profile:

        state["profile"] = {}

        return state

    state["profile"] = {
        "interests": profile.interests or [],
        "wants_more_of": profile.wants_more_of or [],
        "curiosity": profile.curiosity or [],
        "experience_preferences": (
            profile.experience_preferences
            or []
        ),
        "dislikes": profile.dislikes or [],
        "constraints": profile.constraints or [],
        "typical_free_time": (
            profile.typical_free_time
        ),
    }

    return state


def load_recent_activities(
    state: AgentState,
    db: Session,
):

    activities = (
        db.query(Activity)
        .filter(
            Activity.user_id
            == state["user_id"]
        )
        .order_by(
            Activity.created_at.desc()
        )
        .limit(8)
        .all()
    )

    state["recent_activities"] = [
        {
            "id": activity.id,
            "title": activity.title,
            "description": activity.description,
            "category": activity.category,
            "duration_minutes": (
                activity.duration_minutes
            ),
            "status": activity.status,
        }
        for activity in activities
    ]

    return state


def understand_request(
    state: AgentState,
):

    message = state[
        "user_message"
    ].lower()

    if any(
        phrase in message
        for phrase in [
            "don't like",
            "do not like",
            "give me another",
            "another one",
            "different one",
            "something else",
        ]
    ):
        intent = "regenerate"

    elif any(
        phrase in message
        for phrase in [
            "tired",
            "low energy",
            "no energy",
            "exhausted",
        ]
    ):
        intent = "adapt_energy"

    elif any(
        phrase in message
        for phrase in [
            "social",
            "friends",
            "people",
            "meet someone",
        ]
    ):
        intent = "adapt_social"

    elif any(
        phrase in message
        for phrase in [
            "temple",
            "park",
            "restaurant",
            "cafe",
            "shopping",
            "market",
            "bookstore",
            "library",
            "museum",
            "near me",
            "nearby",
        ]
    ):
        intent = "find_place"

    elif any(
        phrase in message
        for phrase in [
            "finished",
            "completed",
            "done with it",
            "i did it",
        ]
    ):
        intent = "completed"

    elif any(
        phrase in message
        for phrase in [
            "minutes",
            "minute",
            "hour",
            "hours",
        ]
    ):
        intent = "adapt_time"

    else:
        intent = "generate"

    state["intent"] = intent

    # Extract a simple place-search query.
    place_query = None

    mappings = {
        "temple": "temple",
        "park": "park",
        "restaurant": "restaurant",
        "cafe": "cafe",
        "shopping": "shopping mall",
        "market": "market",
        "bookstore": "bookstore",
        "library": "library",
        "museum": "museum",
        "gym": "gym",
    }

    for keyword, query in mappings.items():

        if keyword in message:

            place_query = query

            break

    state["place_query"] = place_query

    return state


def get_environment(
    state: AgentState,
):

    from .context_service import (
        get_current_context
    )

    context = get_current_context(
        latitude=state.get("latitude"),
        longitude=state.get("longitude"),
        place_query=state.get(
            "place_query"
        ),
    )

    state["current_context"] = context

    return state


def generate_activity(
    state: AgentState,
):

    profile = state.get(
        "profile",
        {}
    )

    history = state.get(
        "recent_activities",
        []
    )

    context = state.get(
        "current_context",
        {}
    )

    prompt = f"""
You are TouchGrass.

You are a personalized real-world activity agent.

USER PROFILE:
{json.dumps(profile, indent=2)}

RECENT ACTIVITIES:
{json.dumps(history, indent=2)}

USER REQUEST:
{state["user_message"]}

INTENT:
{state.get("intent")}

CURRENT ENVIRONMENT:
{json.dumps(context, indent=2)}

Your job is to create ONE realistic offline experience.

Rules:

1. Respect the user's strongest interests.
2. Respect dislikes and constraints.
3. Never repeatedly suggest the same activity.
4. Respect available time.
5. Respect current weather.
6. If the user asks for a nearby place, use the provided nearby_places.
7. Never invent a nearby place.
8. If a real place is provided, include its name.
9. Prefer activities that require little screen time.
10. If the user wants to go somewhere, combine the place with a meaningful activity.
11. If the user is tired, reduce physical and cognitive effort.
12. If the user wants social activity, prefer social experiences.
13. Give exactly ONE primary recommendation.
14. Keep it practical.
15. The phone should become unnecessary after receiving the challenge.

Return ONLY JSON:

{{
    "title": "short title",
    "description": "what the user should actually do",
    "category": "learn/create/explore/move/connect/relax",
    "duration_minutes": 20,
    "reason": "why this fits",
    "place": {{
        "name": "place name or null",
        "latitude": null,
        "longitude": null,
        "display_name": null
    }}
}}
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are the reasoning engine "
                    "for TouchGrass. Return valid JSON."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.7,
        max_tokens=800,
        response_format={
            "type": "json_object"
        },
    )

    content = (
        response.choices[0]
        .message
        .content
        .strip()
    )

    activity = json.loads(content)

    state["activity"] = activity

    state["response"] = activity.get(
        "reason",
        "",
    )

    return state


def save_activity(
    state: AgentState,
    db: Session,
):

    activity_data = state[
        "activity"
    ]

    activity = Activity(
        user_id=state["user_id"],
        title=activity_data["title"],
        description=activity_data[
            "description"
        ],
        category=activity_data.get(
            "category"
        ),
        duration_minutes=activity_data.get(
            "duration_minutes"
        ),
        context={
            "source": "agent",
            "intent": state.get(
                "intent"
            ),
            "user_message": state.get(
                "user_message",
                "",
            ),
            "reason": activity_data.get(
                "reason",
                "",
            ),
            "place": activity_data.get(
                "place"
            ),
            "environment": state.get(
                "current_context"
            ),
        },
        status="suggested",
    )

    db.add(activity)
    db.commit()
    db.refresh(activity)

    state["activity_id"] = activity.id

    return state


def build_agent(
    db: Session,
):

    graph = StateGraph(
        AgentState
    )

    graph.add_node(
        "load_profile",
        lambda state:
            load_user_profile(
                state,
                db,
            ),
    )

    graph.add_node(
        "load_history",
        lambda state:
            load_recent_activities(
                state,
                db,
            ),
    )

    graph.add_node(
        "understand_request",
        understand_request,
    )

    graph.add_node(
        "get_environment",
        get_environment,
    )

    graph.add_node(
        "generate_activity",
        generate_activity,
    )

    graph.add_node(
        "save_activity",
        lambda state:
            save_activity(
                state,
                db,
            ),
    )

    graph.add_edge(
        START,
        "load_profile",
    )

    graph.add_edge(
        "load_profile",
        "load_history",
    )

    graph.add_edge(
        "load_history",
        "understand_request",
    )

    graph.add_edge(
        "understand_request",
        "get_environment",
    )

    graph.add_edge(
        "get_environment",
        "generate_activity",
    )

    graph.add_edge(
        "generate_activity",
        "save_activity",
    )

    graph.add_edge(
        "save_activity",
        END,
    )

    return graph.compile()