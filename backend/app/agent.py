
import json
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from .ai_service import generate_json
from .models import Activity, ActivityFeedback, ConversationMessage, UserProfile


class AgentState(TypedDict, total=False):
    user_id: int
    user_message: str

    profile: dict[str, Any]
    history: list[dict[str, Any]]
    context: dict[str, Any]

    intent: str
    activity: dict[str, Any]
    reason: str
    error: str


ACTIVITY_SYSTEM_PROMPT = """
You are TouchGrass, a personalized real-world activity agent.

Your primary goal is to help users spend less passive screen time
and engage in meaningful offline activities.

Use the user's profile, previous activity history, available time,
location and other context to create ONE realistic offline challenge.

IMPORTANT RULES:

- Prioritize the user's strongest interests.
- Do not repeatedly recommend the same activity.
- Consider the user's available time.
- Consider location and weather when available.
- Prefer activities requiring little or no screen time.
- Prefer resources the user already has.
- Do not overwhelm the user with choices.
- Give ONE primary challenge.
- Occasionally combine two interests.
- Learn from previous feedback.
- The activity must be realistic and achievable.
- Do not recommend dangerous or illegal activities.
- Do not require expensive equipment unless appropriate.

Return ONLY valid JSON.

Required format:

{
  "title": "short activity title",
  "description": "clear instructions for the activity",
  "category": "learn/create/explore/move/connect/relax",
  "duration_minutes": 30,
  "reason": "why this activity fits the user"
}
"""


def load_profile(
    user_id: int,
    db: Session,
) -> dict[str, Any]:

    profile = (
        db.query(UserProfile)
        .filter(UserProfile.user_id == user_id)
        .first()
    )

    if not profile:
        return {}

    return {
        "interests": profile.interests or [],
        "wants_more_of": profile.wants_more_of or [],
        "curiosity": profile.curiosity or [],
        "experience_preferences": profile.experience_preferences or [],
        "dislikes": profile.dislikes or [],
        "constraints": profile.constraints or [],
        "typical_free_time": profile.typical_free_time or "",
        "adventure_level": profile.adventure_level or "",
    }


def load_history(
    user_id: int,
    db: Session,
) -> list[dict[str, Any]]:

    activities = (
        db.query(Activity)
        .filter(Activity.user_id == user_id)
        .order_by(Activity.created_at.desc())
        .limit(10)
        .all()
    )

    history = []

    for activity in activities:

        feedback = (
            db.query(ActivityFeedback)
            .filter(
                ActivityFeedback.activity_id == activity.id,
                ActivityFeedback.user_id == user_id,
            )
            .order_by(ActivityFeedback.created_at.desc())
            .first()
        )

        history.append(
            {
                "title": activity.title,
                "description": activity.description,
                "category": activity.category,
                "duration_minutes": activity.duration_minutes,
                "status": activity.status,
                "rating": feedback.rating if feedback else None,
                "completed": feedback.completed if feedback else None,
                "comment": feedback.comment if feedback else None,
            }
        )

    return history


def load_user_data(
    state: AgentState,
    db: Session,
) -> AgentState:

    user_id = state["user_id"]

    return {
        **state,
        "profile": load_profile(user_id, db),
        "history": load_history(user_id, db),
    }


def understand_request(
    state: AgentState,
    db: Session,
) -> AgentState:

    return {
        **state,
        "intent": "activity_request",
    }


def generate_activity(
    state: AgentState,
    db: Session,
) -> AgentState:

    profile = state.get("profile", {})
    history = state.get("history", [])
    user_message = state["user_message"]
    context = state.get("context", {})

    user_prompt = f"""
USER REQUEST:
{user_message}

USER PROFILE:
{json.dumps(profile, ensure_ascii=False, indent=2)}

RECENT ACTIVITY HISTORY:
{json.dumps(history, ensure_ascii=False, indent=2)}

CURRENT CONTEXT:
{json.dumps(context, ensure_ascii=False, indent=2)}

Create ONE personalized offline challenge.

Avoid activities that are too similar to recent activities.

Return ONLY the required JSON.
"""

    try:

        activity = generate_json(
            ACTIVITY_SYSTEM_PROMPT,
            user_prompt,
            temperature=0.8,
            max_tokens=700,
        )

        return {
            **state,
            "activity": activity,
            "reason": activity.get("reason", ""),
            "error": "",
        }

    except Exception as exc:

        return {
            **state,
            "error": (
                f"Activity generation failed: "
                f"{type(exc).__name__}: {str(exc)}"
            ),
        }


def validate_activity(
    state: AgentState,
    db: Session,
) -> AgentState:

    activity = state.get("activity")

    if not activity:
        return {
            **state,
            "error": state.get(
                "error",
                "No activity was generated.",
            ),
        }

    title = str(
        activity.get("title", "")
    ).strip()

    description = str(
        activity.get("description", "")
    ).strip()

    if not title or not description:
        return {
            **state,
            "error": "Generated activity was incomplete.",
        }

    try:
        duration = int(
            activity.get(
                "duration_minutes",
                30,
            )
        )
    except (TypeError, ValueError):
        duration = 30

    duration = max(
        5,
        min(duration, 240),
    )

    category = str(
        activity.get(
            "category",
            "explore",
        )
    ).strip().lower()

    allowed_categories = {
        "learn",
        "create",
        "explore",
        "move",
        "connect",
        "relax",
    }

    if category not in allowed_categories:
        category = "explore"

    cleaned_activity = {
        "title": title[:200],
        "description": description[:3000],
        "category": category,
        "duration_minutes": duration,
        "reason": str(
            activity.get(
                "reason",
                "",
            )
        ).strip()[:1000],
    }

    return {
        **state,
        "activity": cleaned_activity,
        "error": "",
    }


def save_activity(
    state: AgentState,
    db: Session,
) -> AgentState:

    activity_data = state.get("activity")

    if not activity_data:
        return state

    if state.get("error"):
        return state

    activity = Activity(
        user_id=state["user_id"],
        title=activity_data["title"],
        description=activity_data["description"],
        category=activity_data["category"],
        duration_minutes=activity_data["duration_minutes"],
        context=state.get("context", {}),
        status="suggested",
    )

    db.add(activity)

    conversation = ConversationMessage(
        user_id=state["user_id"],
        role="user",
        content=state.get("user_message", ""),
    )

    db.add(conversation)

    db.commit()
    db.refresh(activity)

    activity_data["id"] = activity.id

    return {
        **state,
        "activity": activity_data,
    }


def build_agent_graph(
    db: Session,
):

    graph = StateGraph(AgentState)

    graph.add_node(
        "load_user_data",
        lambda state: load_user_data(
            state,
            db,
        ),
    )

    graph.add_node(
        "understand_request",
        lambda state: understand_request(
            state,
            db,
        ),
    )

    graph.add_node(
        "generate_activity",
        lambda state: generate_activity(
            state,
            db,
        ),
    )

    graph.add_node(
        "validate_activity",
        lambda state: validate_activity(
            state,
            db,
        ),
    )

    graph.add_node(
        "save_activity",
        lambda state: save_activity(
            state,
            db,
        ),
    )

    graph.add_edge(
        START,
        "load_user_data",
    )

    graph.add_edge(
        "load_user_data",
        "understand_request",
    )

    graph.add_edge(
        "understand_request",
        "generate_activity",
    )

    graph.add_edge(
        "generate_activity",
        "validate_activity",
    )

    graph.add_edge(
        "validate_activity",
        "save_activity",
    )

    graph.add_edge(
        "save_activity",
        END,
    )

    return graph.compile()


def run_agent(
    user_id: int,
    message: str,
    db: Session,
    context: dict[str, Any] | None = None,
) -> AgentState:

    graph = build_agent_graph(db)

    initial_state: AgentState = {
        "user_id": user_id,
        "user_message": message,
        "context": context or {},
    }

    return graph.invoke(
        initial_state
    )

