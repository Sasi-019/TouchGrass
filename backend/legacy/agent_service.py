import json
from typing import Any, TypedDict

from groq import Groq
from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from .ai_service import GROQ_MODEL, client
from .models import (
    Activity,
    ConversationMessage,
    UserProfile,
)


# ============================================================
# LANGGRAPH STATE
# ============================================================

class AgentState(TypedDict, total=False):
    user_id: int
    user_message: str

    latitude: float | None
    longitude: float | None

    profile: dict[str, Any]
    recent_activities: list[dict[str, Any]]
    conversation_history: list[dict[str, str]]

    intent: str | None
    need_weather: bool
    need_places: bool
    place_category: str | None

    weather: dict[str, Any] | None
    nearby_places: list[dict[str, Any]]

    activity: dict[str, Any] | None
    activity_id: int | None

    response: str | None
    error: str | None


# ============================================================
# HELPERS
# ============================================================

def _safe_json(value: Any) -> Any:
    """
    Ensure SQLAlchemy JSON values are converted into normal
    Python values before sending them to the LLM.
    """

    if value is None:
        return None

    if isinstance(value, (dict, list, str, int, float, bool)):
        return value

    try:
        return json.loads(json.dumps(value))
    except Exception:
        return str(value)


def _profile_to_dict(profile: UserProfile | None) -> dict[str, Any]:
    if profile is None:
        return {
            "interests": [],
            "wants_more_of": [],
            "curiosity": [],
            "experience_preferences": [],
            "dislikes": [],
            "constraints": [],
            "typical_free_time": "",
            "adventure_level": "",
        }

    return {
        "interests": _safe_json(profile.interests) or [],
        "wants_more_of": _safe_json(profile.wants_more_of) or [],
        "curiosity": _safe_json(profile.curiosity) or [],
        "experience_preferences": (
            _safe_json(profile.experience_preferences) or []
        ),
        "dislikes": _safe_json(profile.dislikes) or [],
        "constraints": _safe_json(profile.constraints) or [],
        "typical_free_time": profile.typical_free_time or "",
        "adventure_level": profile.adventure_level or "",
    }


# ============================================================
# NODE 1 — LOAD PROFILE
# ============================================================

def load_profile(
    state: AgentState,
    db: Session,
) -> AgentState:

    user_id = state["user_id"]

    profile = (
        db.query(UserProfile)
        .filter(
            UserProfile.user_id == user_id
        )
        .first()
    )

    return {
        **state,
        "profile": _profile_to_dict(profile),
    }


# ============================================================
# NODE 2 — LOAD RECENT ACTIVITY HISTORY
# ============================================================

def load_history(
    state: AgentState,
    db: Session,
) -> AgentState:

    user_id = state["user_id"]

    activities = (
        db.query(Activity)
        .filter(
            Activity.user_id == user_id
        )
        .order_by(
            Activity.created_at.desc()
        )
        .limit(10)
        .all()
    )

    recent_activities = []

    for activity in activities:
        recent_activities.append(
            {
                "id": activity.id,
                "title": activity.title,
                "description": activity.description,
                "category": activity.category,
                "duration_minutes": (
                    activity.duration_minutes
                ),
                "status": activity.status,
                "context": _safe_json(
                    activity.context
                ),
            }
        )

    return {
        **state,
        "recent_activities": recent_activities,
    }


# ============================================================
# NODE 3 — LOAD CONVERSATION HISTORY
# ============================================================

def load_conversation(
    state: AgentState,
    db: Session,
) -> AgentState:

    user_id = state["user_id"]

    messages = (
        db.query(ConversationMessage)
        .filter(
            ConversationMessage.user_id == user_id
        )
        .order_by(
            ConversationMessage.created_at.desc()
        )
        .limit(12)
        .all()
    )

    messages.reverse()

    history = [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in messages
    ]

    return {
        **state,
        "conversation_history": history,
    }


# ============================================================
# NODE 4 — UNDERSTAND USER REQUEST
# ============================================================

INTENT_SYSTEM_PROMPT = """
You are the intent and context analysis component of TouchGrass.

TouchGrass helps people spend less passive screen time and do
meaningful real-world activities.

Analyze the user's latest message using the provided profile,
activity history, and conversation history.

Choose exactly ONE intent:

generate_activity
regenerate_activity
adapt_activity
find_place
general_chat
profile_question

Also determine whether current weather is useful and whether
nearby places are useful.

Possible place categories:

park
restaurant
temple
shopping
nature
cafe
outdoor
other

Rules:

- If the user asks for something to do, use generate_activity.
- If the user asks for another/different idea, use regenerate_activity.
- If the user wants an existing idea changed because of time,
  energy, weather, distance, or constraints, use adapt_activity.
- If the user asks for nearby locations, use find_place.
- If the user asks about their TouchGrass profile, use profile_question.
- Use general_chat for normal conversation.
- Weather is useful when outdoor activity, weather conditions,
  rain, heat, cold, or going outside matter.
- Places are useful when the user wants to go somewhere or asks
  for nearby recommendations.
- Never claim that location exists if coordinates were not supplied.
- Return ONLY valid JSON.

Return exactly:

{
  "intent": "generate_activity",
  "need_weather": false,
  "need_places": false,
  "place_category": null
}
"""


def understand_request(
    state: AgentState,
) -> AgentState:

    profile = state.get("profile", {})
    history = state.get("recent_activities", [])
    conversation = state.get(
        "conversation_history",
        [],
    )

    latitude = state.get("latitude")
    longitude = state.get("longitude")

    user_message = state["user_message"]

    prompt = f"""
USER MESSAGE:
{user_message}

USER PROFILE:
{json.dumps(profile, ensure_ascii=False)}

RECENT ACTIVITIES:
{json.dumps(history, ensure_ascii=False)}

RECENT CONVERSATION:
{json.dumps(conversation, ensure_ascii=False)}

CURRENT LOCATION:
latitude={latitude}
longitude={longitude}
"""

    try:
        result = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": INTENT_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.1,
            max_tokens=300,
            response_format={
                "type": "json_object",
            },
        )

        content = result.choices[0].message.content

        if not content:
            raise ValueError(
                "Empty intent response"
            )

        parsed = json.loads(content)

    except Exception as exc:
        print(
            "Intent analysis error:",
            exc,
        )

        # Safe fallback.
        parsed = {
            "intent": "generate_activity",
            "need_weather": False,
            "need_places": False,
            "place_category": None,
        }

    valid_intents = {
        "generate_activity",
        "regenerate_activity",
        "adapt_activity",
        "find_place",
        "general_chat",
        "profile_question",
    }

    intent = parsed.get(
        "intent",
        "generate_activity",
    )

    if intent not in valid_intents:
        intent = "generate_activity"

    need_weather = bool(
        parsed.get(
            "need_weather",
            False,
        )
    )

    need_places = bool(
        parsed.get(
            "need_places",
            False,
        )
    )

    place_category = parsed.get(
        "place_category"
    )

    if place_category:
        place_category = str(
            place_category
        ).strip().lower()

    # Places require coordinates.
    if (
        state.get("latitude") is None
        or state.get("longitude") is None
    ):
        need_places = False

    return {
        **state,
        "intent": intent,
        "need_weather": need_weather,
        "need_places": need_places,
        "place_category": place_category,
    }


# ============================================================
# NODE 5 — WEATHER TOOL
# ============================================================

def weather_tool(
    state: AgentState,
) -> AgentState:

    if not state.get("need_weather"):
        return {
            **state,
            "weather": None,
        }

    latitude = state.get("latitude")
    longitude = state.get("longitude")

    if latitude is None or longitude is None:
        return {
            **state,
            "weather": {
                "available": False,
                "reason": (
                    "Location was not provided."
                ),
            },
        }

    try:
        from .tools.weather import get_weather

        weather = get_weather(
            latitude=latitude,
            longitude=longitude,
        )

        return {
            **state,
            "weather": weather,
        }

    except Exception as exc:
        print(
            "Weather tool error:",
            exc,
        )

        return {
            **state,
            "weather": {
                "available": False,
                "reason": (
                    "Weather information is temporarily "
                    "unavailable."
                ),
            },
        }


# ============================================================
# NODE 6 — PLACES TOOL
# ============================================================

def places_tool(
    state: AgentState,
) -> AgentState:

    if not state.get("need_places"):
        return {
            **state,
            "nearby_places": [],
        }

    latitude = state.get("latitude")
    longitude = state.get("longitude")

    if latitude is None or longitude is None:
        return {
            **state,
            "nearby_places": [],
        }

    category = (
        state.get("place_category")
        or "outdoor"
    )

    try:
        from .tools.places import find_nearby_places

        places = find_nearby_places(
            latitude=latitude,
            longitude=longitude,
            category=category,
        )

        return {
            **state,
            "nearby_places": places,
        }

    except Exception as exc:
        print(
            "Places tool error:",
            exc,
        )

        return {
            **state,
            "nearby_places": [],
        }


# ============================================================
# NODE 7 — GENERAL CHAT
# ============================================================

def general_chat(
    state: AgentState,
) -> AgentState:

    profile = state.get(
        "profile",
        {},
    )

    user_message = state[
        "user_message"
    ]

    system_prompt = """
You are TouchGrass, a friendly real-world activity agent.

Your goal is to help the user spend less passive screen time
and engage in meaningful offline experiences.

For normal conversation:

- Be concise.
- Be warm and natural.
- Do not overwhelm the user.
- Do not produce a large list of activities.
- If the user clearly wants an activity, let the activity
  generation flow handle it.
- Use the user's known profile when relevant.
"""

    prompt = f"""
USER PROFILE:
{json.dumps(profile, ensure_ascii=False)}

USER MESSAGE:
{user_message}
"""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.5,
            max_tokens=500,
        )

        text = (
            response.choices[0]
            .message.content
            or ""
        ).strip()

        return {
            **state,
            "response": text,
        }

    except Exception as exc:
        print(
            "General chat error:",
            exc,
        )

        return {
            **state,
            "response": (
                "I'm having trouble responding right now. "
                "Please try again in a moment."
            ),
        }


# ============================================================
# NODE 8 — PROFILE QUESTION
# ============================================================

def profile_question(
    state: AgentState,
) -> AgentState:

    profile = state.get(
        "profile",
        {},
    )

    user_message = state[
        "user_message"
    ]

    prompt = f"""
You are TouchGrass.

The user is asking about their personal TouchGrass profile.

PROFILE:
{json.dumps(profile, ensure_ascii=False)}

USER QUESTION:
{user_message}

Answer naturally and briefly.

Do not invent information that is not in the profile.
"""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                }
            ],
            temperature=0.3,
            max_tokens=500,
        )

        text = (
            response.choices[0]
            .message.content
            or ""
        ).strip()

        return {
            **state,
            "response": text,
        }

    except Exception as exc:
        print(
            "Profile question error:",
            exc,
        )

        return {
            **state,
            "response": (
                "I couldn't read your profile right now."
            ),
        }


# ============================================================
# NODE 9 — GENERATE ACTIVITY
# ============================================================

ACTIVITY_SYSTEM_PROMPT = """
You are TouchGrass, a personalized real-world activity agent.

Your primary goal is to help users spend less passive screen
time and engage in meaningful offline activities.

You have access to:

1. The user's long-term interests.
2. What they want more of.
3. Their curiosity.
4. Their preferred experience types.
5. Their dislikes and constraints.
6. Their typical free time.
7. Their previous activities.
8. Their current request.
9. Current weather when available.
10. Nearby places when available.

IMPORTANT RULES:

- Prioritize the user's strongest interests.
- Do not repeatedly recommend the same activity.
- Consider the user's available time.
- Consider weather and location.
- Never suggest an activity that is impractical for current
  conditions.
- Prefer little or no screen time.
- Prefer resources the user already has.
- Do not require unnecessary purchases.
- Respect dislikes and constraints.
- Occasionally combine two interests to create something new.
- Give ONE primary challenge.
- Make the activity concrete and actionable.
- Encourage the user to put the phone away after receiving it.
- Keep the challenge achievable.
- If nearby places are provided and relevant, use them.
- Never invent a place that is not in the provided results.

Return ONLY valid JSON:

{
  "title": "short activity title",
  "description": "clear actionable challenge",
  "category": "create/explore/learn/move/connect/relax",
  "duration_minutes": 20,
  "reason": "short explanation of personalization"
}
"""


def generate_activity(
    state: AgentState,
) -> AgentState:

    profile = state.get(
        "profile",
        {},
    )

    history = state.get(
        "recent_activities",
        [],
    )

    conversation = state.get(
        "conversation_history",
        [],
    )

    weather = state.get(
        "weather",
    )

    places = state.get(
        "nearby_places",
        [],
    )

    user_message = state[
        "user_message"
    ]

    prompt = f"""
USER REQUEST:
{user_message}

INTENT:
{state.get("intent")}

USER PROFILE:
{json.dumps(profile, ensure_ascii=False)}

RECENT ACTIVITIES:
{json.dumps(history, ensure_ascii=False)}

RECENT CONVERSATION:
{json.dumps(conversation, ensure_ascii=False)}

CURRENT WEATHER:
{json.dumps(weather, ensure_ascii=False)}

NEARBY PLACES:
{json.dumps(places, ensure_ascii=False)}

CURRENT LOCATION:
latitude={state.get("latitude")}
longitude={state.get("longitude")}
"""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": ACTIVITY_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.7,
            max_tokens=700,
            response_format={
                "type": "json_object",
            },
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError(
                "Empty activity response"
            )

        activity = json.loads(content)

        required = [
            "title",
            "description",
            "category",
            "duration_minutes",
            "reason",
        ]

        for field in required:
            if field not in activity:
                raise ValueError(
                    f"Missing activity field: {field}"
                )

        return {
            **state,
            "activity": activity,
            "response": activity.get(
                "reason",
                "",
            ),
        }

    except Exception as exc:
        print(
            "Activity generation error:",
            exc,
        )

        return {
            **state,
            "activity": {
                "title": "A 10-Minute Reset Walk",
                "description": (
                    "Step outside or walk around your "
                    "building for 10 minutes. Notice five "
                    "things you normally ignore, then put "
                    "your phone away and continue walking."
                ),
                "category": "move",
                "duration_minutes": 10,
                "reason": (
                    "A simple offline activity while the "
                    "AI service is temporarily unavailable."
                ),
            },
            "response": (
                "I created a simple offline challenge "
                "you can start immediately."
            ),
        }


# ============================================================
# NODE 10 — SAVE CONVERSATION + ACTIVITY
# ============================================================

def save_results(
    state: AgentState,
    db: Session,
) -> AgentState:

    user_id = state["user_id"]

    user_message = state[
        "user_message"
    ]

    # Save the user's message.
    db.add(
        ConversationMessage(
            user_id=user_id,
            role="user",
            content=user_message,
        )
    )

    activity_data = state.get(
        "activity"
    )

    activity_id = None

    if activity_data:
        context = {
            "source": "langgraph_agent",
            "intent": state.get("intent"),
            "user_message": user_message,
            "latitude": state.get("latitude"),
            "longitude": state.get("longitude"),
            "weather": state.get("weather"),
            "nearby_places": state.get(
                "nearby_places",
                [],
            ),
            "reason": activity_data.get(
                "reason",
                "",
            ),
        }

        activity = Activity(
            user_id=user_id,
            title=str(
                activity_data.get(
                    "title",
                    "TouchGrass Challenge",
                )
            ),
            description=str(
                activity_data.get(
                    "description",
                    "",
                )
            ),
            category=activity_data.get(
                "category"
            ),
            duration_minutes=activity_data.get(
                "duration_minutes"
            ),
            context=context,
            status="suggested",
        )

        db.add(activity)

        db.flush()

        activity_id = activity.id

        # Save assistant activity response as conversation memory.
        assistant_content = (
            f"{activity.title}: "
            f"{activity.description}"
        )

        db.add(
            ConversationMessage(
                user_id=user_id,
                role="assistant",
                content=assistant_content,
            )
        )

    elif state.get("response"):
        db.add(
            ConversationMessage(
                user_id=user_id,
                role="assistant",
                content=state["response"],
            )
        )

    db.commit()

    return {
        **state,
        "activity_id": activity_id,
    }


# ============================================================
# GRAPH ROUTING
# ============================================================

def route_after_understanding(
    state: AgentState,
) -> str:

    intent = state.get(
        "intent",
        "generate_activity",
    )

    if intent == "general_chat":
        return "general_chat"

    if intent == "profile_question":
        return "profile_question"

    # All activity-related intents use the same generation
    # pipeline. The intent is passed to the LLM so it can adapt
    # the challenge appropriately.
    return "activity_context"


# ============================================================
# GRAPH ROUTING FOR TOOLS
# ============================================================

def route_tools(
    state: AgentState,
) -> str:

    if state.get("need_weather"):
        return "weather"

    if state.get("need_places"):
        return "places"

    return "generate_activity"


def route_after_weather(
    state: AgentState,
) -> str:

    if state.get("need_places"):
        return "places"

    return "generate_activity"


# ============================================================
# BUILD LANGGRAPH
# ============================================================

def build_agent(
    db: Session,
):
    """
    Build the TouchGrass LangGraph agent.

    The graph is intentionally created per request because the
    database session belongs to the current FastAPI request.
    """

    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node(
        "load_profile",
        lambda state: load_profile(
            state,
            db,
        ),
    )

    graph.add_node(
        "load_history",
        lambda state: load_history(
            state,
            db,
        ),
    )

    graph.add_node(
        "load_conversation",
        lambda state: load_conversation(
            state,
            db,
        ),
    )

    graph.add_node(
        "understand_request",
        understand_request,
    )

    graph.add_node(
        "weather",
        weather_tool,
    )

    graph.add_node(
        "places",
        places_tool,
    )

    graph.add_node(
        "generate_activity",
        generate_activity,
    )

    graph.add_node(
        "general_chat",
        general_chat,
    )

    graph.add_node(
        "profile_question",
        profile_question,
    )

    graph.add_node(
        "save_results",
        lambda state: save_results(
            state,
            db,
        ),
    )

    # Initial flow
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
        "load_conversation",
    )

    graph.add_edge(
        "load_conversation",
        "understand_request",
    )

    # Decide whether this is conversation or an activity task.
    graph.add_conditional_edges(
        "understand_request",
        route_after_understanding,
        {
            "general_chat": "general_chat",
            "profile_question": "profile_question",
            "activity_context": "generate_activity",
        },
    )

    # Activity generation.
    #
    # Weather/place tools are executed before final activity
    # generation when the intent classifier requested them.
    #
    # We use an intermediate routing node represented by the
    # generate_activity node's input context. To keep the graph
    # simple and deterministic, weather/place execution is
    # selected through a small conditional branch below.

    # Rewire activity context using a lightweight router node.
    graph.add_node(
        "activity_context",
        lambda state: state,
    )

    graph.add_edge(
        "activity_context",
        "generate_activity",
    )

    # The conditional branch above directly enters activity
    # generation. For requests requiring tools, we instead need
    # the tool nodes first. This second graph path is represented
    # below using a conditional edge from understand_request.
    #
    # LangGraph does not permit two different destinations for the
    # same key in a conditional mapping, so we use a dedicated
    # routing node in the actual execution path.

    # Rebuild the activity routing cleanly.
    #
    # The graph accepts the following additional route:
    # understand_request -> activity_context
    # activity_context -> weather / places / generate_activity

    # Remove the direct edge above by using conditional routing
    # from activity_context.
    graph.add_conditional_edges(
        "activity_context",
        route_tools,
        {
            "weather": "weather",
            "places": "places",
            "generate_activity": "generate_activity",
        },
    )

    graph.add_edge(
        "weather",
        "places",
    )

    graph.add_conditional_edges(
        "weather",
        route_after_weather,
        {
            "places": "places",
            "generate_activity": "generate_activity",
        },
    )

    graph.add_edge(
        "places",
        "generate_activity",
    )

    # Conversation paths
    graph.add_edge(
        "general_chat",
        "save_results",
    )

    graph.add_edge(
        "profile_question",
        "save_results",
    )

    # Final activity path
    graph.add_edge(
        "generate_activity",
        "save_results",
    )

    graph.add_edge(
        "save_results",
        END,
    )

    return graph.compile()