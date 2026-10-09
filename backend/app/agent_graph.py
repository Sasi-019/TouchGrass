
import json
from typing import Any, TypedDict

from langgraph.graph import StateGraph, START, END
from sqlalchemy.orm import Session

from .ai_service import generate_json
from .models import Activity, ConversationMessage, UserProfile
from .real_world_tools import get_weather, search_nearby_places


class TouchGrassState(TypedDict, total=False):
    user_id: int
    user_message: str
    profile: dict[str, Any]
    conversation_history: list[dict[str, Any]]
    activity_history: list[dict[str, Any]]
    current_context: dict[str, Any]
    agent_context: dict[str, Any]
    tool_plan: dict[str, Any]
    tool_results: list[dict[str, Any]]
    intent: str
    reply: str
    activity: dict[str, Any] | None
    reason: str | None
    error: str


PLANNER_PROMPT = """
You are the tool planner for TouchGrass.

Choose tools only when they are useful for answering the latest message.

Available tools:
- weather: current weather and today's forecast for a known city or coordinates.
- nearby_places: find real nearby parks, cafes, restaurants, museums, and attractions.

Return ONLY valid JSON:
{
  "tools": [],
  "location": null,
  "category": "all",
  "needs_location": false
}

Rules:
- Use "weather" for current weather, temperature, rain, or forecast questions.
- Use "nearby_places" for nearby places, outings, or location recommendations.
- Both tools can be selected for an outing when weather is relevant.
- Use the location explicitly stated by the user, or a city clearly established
  in recent conversation history.
- If the user says "near me" and usable latitude/longitude are supplied,
  use those coordinates instead of asking for a city.
- If location is essential but unavailable, set needs_location=true.
- Do not call tools for ordinary conversation.
- For places, category can be all, parks, cafes, museums, or attractions.
- Never guess a city.
"""


AGENT_SYSTEM_PROMPT = """
You are TouchGrass, a thoughtful conversational real-world activity agent.

Use the user's saved profile, recent conversation, past activities, and
real tool results to answer naturally.

Intent:
- chat: greetings, normal questions, follow-ups, explanations.
- activity: the user wants a specific activity, plan, challenge, or outing.
- clarify: essential information is missing.

Rules:
- Use weather and places results when provided.
- Never invent live weather, places, distances, opening hours, or availability.
- If a tool fails, explain that briefly and still help where possible.
- If location is missing, ask for it once.
- Reuse the city from recent conversation history when clear.
- For a limited break, account for travel time and the time needed to return.
- Do not create an activity for every ordinary question.
- Replies must be concise and conversational.
- If recommending a place, use names from the actual tool results.
- Do not claim a place is open unless reliable opening-hour information is supplied.
- Return ONLY one valid JSON object, with no Markdown fences.

Normal conversation:
{
  "intent": "chat",
  "reply": "Natural response.",
  "reason": null,
  "activity": null
}

Activity:
{
  "intent": "activity",
  "reply": "Short introduction.",
  "reason": "Why this fits the user.",
  "activity": {
    "title": "Specific activity title",
    "description": "Actionable instructions using verified results where applicable.",
    "category": "exploration",
    "duration_minutes": 30,
    "reason": "Why this fits the user."
  }
}

Clarification:
{
  "intent": "clarify",
  "reply": "One concise question.",
  "reason": null,
  "activity": null
}

Allowed categories: creativity, outdoors, learning, fitness, social,
relaxation, exploration, food, other.
"""


def load_profile_node(state: TouchGrassState, db: Session):
    profile = (
        db.query(UserProfile)
        .filter(UserProfile.user_id == state["user_id"])
        .first()
    )

    data = {}
    if profile:
        data = {
            "interests": profile.interests or [],
            "wants_more_of": profile.wants_more_of or [],
            "curiosity": profile.curiosity or [],
            "experience_preferences": profile.experience_preferences or [],
            "dislikes": profile.dislikes or [],
            "constraints": profile.constraints or [],
            "typical_free_time": profile.typical_free_time or "",
            "adventure_level": profile.adventure_level or "moderate",
        }

    return {**state, "profile": data}


def load_conversation_node(state: TouchGrassState, db: Session):
    messages = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.user_id == state["user_id"])
        .order_by(
            ConversationMessage.created_at.desc(),
            ConversationMessage.id.desc(),
        )
        .limit(12)
        .all()
    )
    messages.reverse()

    history = [
        {"role": item.role, "content": item.content}
        for item in messages
    ]
    return {**state, "conversation_history": history}


def load_activity_history_node(state: TouchGrassState, db: Session):
    activities = (
        db.query(Activity)
        .filter(Activity.user_id == state["user_id"])
        .order_by(
            Activity.created_at.desc(),
            Activity.id.desc(),
        )
        .limit(10)
        .all()
    )

    history = [
        {
            "title": item.title,
            "description": item.description,
            "category": item.category,
            "duration_minutes": item.duration_minutes,
            "status": item.status,
        }
        for item in activities
    ]
    return {**state, "activity_history": history}


def build_context_node(state: TouchGrassState):
    context = {
        "user_profile": state.get("profile", {}),
        "recent_conversation": state.get("conversation_history", []),
        "recent_activities": state.get("activity_history", []),
        "request_context": state.get("current_context", {}),
        "current_message": state.get("user_message", ""),
    }
    return {**state, "agent_context": context}


def plan_tools_node(state: TouchGrassState):
    context = state.get("agent_context", {})
    request_context = context.get("request_context", {})

    planner_input = {
        "recent_conversation": context.get("recent_conversation", []),
        "current_message": context.get("current_message", ""),
        "location_context": {
            "city": request_context.get("city"),
            "latitude": request_context.get("latitude"),
            "longitude": request_context.get("longitude"),
        },
    }

    plan = generate_json(
        system_prompt=PLANNER_PROMPT,
        user_prompt=json.dumps(planner_input, ensure_ascii=False),
        temperature=0,
        max_tokens=300,
    )

    if not isinstance(plan, dict):
        plan = {}

    allowed_tools = {"weather", "nearby_places"}
    requested = plan.get("tools", [])
    if not isinstance(requested, list):
        requested = []

    tools = [name for name in requested if name in allowed_tools]
    location = plan.get("location")
    if not isinstance(location, str) or not location.strip():
        location = request_context.get("city")

    return {
        **state,
        "tool_plan": {
            "tools": tools,
            "location": location.strip() if isinstance(location, str) else None,
            "category": plan.get("category", "all"),
            "needs_location": bool(plan.get("needs_location", False)),
        },
        "tool_results": [],
    }


def execute_tools_node(state: TouchGrassState):
    plan = state.get("tool_plan", {})
    context = state.get("current_context", {})

    latitude = context.get("latitude")
    longitude = context.get("longitude")
    location = plan.get("location")
    results = []

    if plan.get("needs_location") and not (
        latitude is not None and longitude is not None
    ) and not location:
        return {
            **state,
            "tool_results": [{
                "tool": "location",
                "ok": False,
                "needs_location": True,
                "error": "Ask the user which city or area they mean.",
            }],
        }

    for tool_name in plan.get("tools", []):
        if tool_name == "weather":
            result = get_weather(
                location=location,
                latitude=latitude,
                longitude=longitude,
            )
        elif tool_name == "nearby_places":
            result = search_nearby_places(
                location=location,
                latitude=latitude,
                longitude=longitude,
                category=plan.get("category", "all"),
            )
        else:
            continue

        results.append({"tool": tool_name, **result})

    return {**state, "tool_results": results}


def generate_response_node(state: TouchGrassState):
    context = {
        **state.get("agent_context", {}),
        "tool_results": state.get("tool_results", []),
    }

    prompt = f"""
Answer the user's latest message using the context and tool results below.

CONTEXT AND TOOL RESULTS:
{json.dumps(context, ensure_ascii=False, indent=2)}

Important:
- Tool results are the source of truth for live weather and places.
- If a tool failed, do not fabricate its result.
- If the user supplied a city earlier, use it when it is clearly relevant.
- Ask a concise location question only when the location cannot be resolved.
- Normal weather questions should receive a direct answer, not an activity card.
- For outing requests, provide a useful plan that fits the user's available time.

LATEST USER MESSAGE:
{state.get("user_message", "")}
"""

    result = generate_json(
        system_prompt=AGENT_SYSTEM_PROMPT,
        user_prompt=prompt,
        temperature=0.3,
        max_tokens=1400,
    )

    if not isinstance(result, dict):
        raise ValueError("The AI service did not return a JSON object.")

    return {
        **state,
        "intent": result.get("intent", "chat"),
        "reply": result.get("reply", ""),
        "reason": result.get("reason"),
        "activity": result.get("activity"),
        "error": "",
    }


def validate_response_node(state: TouchGrassState):
    intent = state.get("intent", "chat")
    reply = state.get("reply")
    reason = state.get("reason")
    activity = state.get("activity")

    if intent not in {"chat", "activity", "clarify"}:
        intent = "chat"

    if not isinstance(reply, str) or not reply.strip():
        raise ValueError("The agent generated an empty reply.")

    if intent == "activity":
        if not isinstance(activity, dict):
            raise ValueError("Activity intent requires an activity object.")

        title = activity.get("title")
        description = activity.get("description")

        if not isinstance(title, str) or not title.strip():
            raise ValueError("The generated activity has no valid title.")
        if not isinstance(description, str) or not description.strip():
            raise ValueError("The generated activity has no valid description.")

        allowed_categories = {
            "creativity", "outdoors", "learning", "fitness", "social",
            "relaxation", "exploration", "food", "other",
        }
        category = activity.get("category", "other")
        if category not in allowed_categories:
            category = "other"

        duration = activity.get("duration_minutes")
        try:
            duration = int(duration) if duration is not None else None
        except (ValueError, TypeError):
            duration = None

        if duration is not None and duration <= 0:
            duration = None

        activity = {
            "title": title.strip(),
            "description": description.strip(),
            "category": category,
            "duration_minutes": duration,
            "reason": activity.get("reason") or reason or "",
        }
    else:
        activity = None

    return {
        **state,
        "intent": intent,
        "reply": reply.strip(),
        "reason": reason,
        "activity": activity,
    }


def persist_response_node(state: TouchGrassState, db: Session):
    try:
        saved_activity = None
        activity_data = state.get("activity")

        if state.get("intent") == "activity" and activity_data:
            record = Activity(
                user_id=state["user_id"],
                title=activity_data["title"],
                description=activity_data["description"],
                category=activity_data.get("category"),
                duration_minutes=activity_data.get("duration_minutes"),
                context={
                    "reason": activity_data.get("reason"),
                    "request": state.get("user_message", ""),
                },
                status="suggested",
            )
            db.add(record)
            db.flush()
            saved_activity = {**activity_data, "id": record.id}

        db.add_all([
            ConversationMessage(
                user_id=state["user_id"],
                role="user",
                content=state["user_message"],
            ),
            ConversationMessage(
                user_id=state["user_id"],
                role="assistant",
                content=state["reply"],
            ),
        ])
        db.commit()

        return {
            **state,
            "activity": saved_activity,
            "error": "",
        }
    except Exception:
        db.rollback()
        raise


def create_touchgrass_graph(db: Session):
    graph = StateGraph(TouchGrassState)

    graph.add_node("load_profile", lambda s: load_profile_node(s, db))
    graph.add_node("load_conversation", lambda s: load_conversation_node(s, db))
    graph.add_node(
        "load_activity_history",
        lambda s: load_activity_history_node(s, db),
    )
    graph.add_node("build_context", build_context_node)
    graph.add_node("plan_tools", plan_tools_node)
    graph.add_node("execute_tools", execute_tools_node)
    graph.add_node("generate_response", generate_response_node)
    graph.add_node("validate_response", validate_response_node)
    graph.add_node("persist_response", lambda s: persist_response_node(s, db))

    graph.add_edge(START, "load_profile")
    graph.add_edge("load_profile", "load_conversation")
    graph.add_edge("load_conversation", "load_activity_history")
    graph.add_edge("load_activity_history", "build_context")
    graph.add_edge("build_context", "plan_tools")
    graph.add_edge("plan_tools", "execute_tools")
    graph.add_edge("execute_tools", "generate_response")
    graph.add_edge("generate_response", "validate_response")
    graph.add_edge("validate_response", "persist_response")
    graph.add_edge("persist_response", END)

    return graph.compile()


def run_touchgrass_graph(
    user_id: int,
    user_message: str,
    db: Session,
    current_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    message = user_message.strip()
    if not message:
        raise ValueError("The user message cannot be empty.")

    graph = create_touchgrass_graph(db)
    initial_state: TouchGrassState = {
        "user_id": user_id,
        "user_message": message,
        "current_context": current_context or {},
    }
    return graph.invoke(initial_state)
