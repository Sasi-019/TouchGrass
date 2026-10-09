
import json
from typing import Any, TypedDict

from langgraph.graph import StateGraph, START, END
from sqlalchemy.orm import Session

from .ai_service import generate_json
from .models import Activity, ActivityFeedback, UserProfile


# ============================================================
# STATE
# ============================================================

class TouchGrassState(TypedDict, total=False):
    user_id: int
    user_message: str

    profile: dict[str, Any]
    history: list[dict[str, Any]]
    current_context: dict[str, Any]

    activity: dict[str, Any]
    error: str


# ============================================================
# PROMPT
# ============================================================

TOUCHGRASS_PROMPT = """
You are TouchGrass, a personalized real-world activity agent.

Your goal is to help the user spend less passive screen time and
do meaningful activities in the real world.

You receive:

- long-term interests
- things the user wants more of
- curiosity
- experience preferences
- dislikes
- constraints
- typical available time
- adventure level
- previous activities
- current context
- the user's current request

Create exactly ONE realistic offline activity.

Rules:

1. Prioritize strong interests.
2. Respect dislikes and constraints.
3. Respect available time.
4. Avoid recently suggested activities.
5. Prefer activities requiring little or no screen time.
6. Prefer things the user can do with resources they already have.
7. Consider current context when available.
8. Occasionally combine two interests.
9. Do not give a list of activities.
10. Do not suggest dangerous or illegal activities.

Return ONLY JSON.

Format:

{
    "title": "short activity name",
    "description": "clear instructions telling the user exactly what to do",
    "category": "learn/create/explore/move/connect/relax",
    "duration_minutes": 30,
    "reason": "short explanation of why this fits the user"
}
"""


# ============================================================
# NODE 1 — LOAD PROFILE
# ============================================================

def load_profile_node(
    state: TouchGrassState,
    db: Session,
) -> TouchGrassState:

    user_id = state["user_id"]

    profile = (
        db.query(UserProfile)
        .filter(UserProfile.user_id == user_id)
        .first()
    )

    if profile is None:
        return {
            **state,
            "profile": {},
        }

    profile_data = {
        "interests": profile.interests or [],
        "wants_more_of": profile.wants_more_of or [],
        "curiosity": profile.curiosity or [],
        "experience_preferences": (
            profile.experience_preferences or []
        ),
        "dislikes": profile.dislikes or [],
        "constraints": profile.constraints or [],
        "typical_free_time": (
            profile.typical_free_time or ""
        ),
        "adventure_level": (
            profile.adventure_level or ""
        ),
    }

    return {
        **state,
        "profile": profile_data,
    }


# ============================================================
# NODE 2 — LOAD HISTORY
# ============================================================

def load_history_node(
    state: TouchGrassState,
    db: Session,
) -> TouchGrassState:

    user_id = state["user_id"]

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
            .order_by(
                ActivityFeedback.created_at.desc()
            )
            .first()
        )

        history.append(
            {
                "title": activity.title,
                "category": activity.category,
                "duration_minutes": (
                    activity.duration_minutes
                ),
                "status": activity.status,
                "rating": (
                    feedback.rating
                    if feedback
                    else None
                ),
                "completed": (
                    feedback.completed
                    if feedback
                    else None
                ),
                "comment": (
                    feedback.comment
                    if feedback
                    else None
                ),
            }
        )

    return {
        **state,
        "history": history,
    }


# ============================================================
# NODE 3 — BUILD CURRENT CONTEXT
# ============================================================

def build_context_node(
    state: TouchGrassState,
    db: Session,
) -> TouchGrassState:

    context = state.get(
        "current_context",
        {},
    )

    return {
        **state,
        "current_context": context,
    }


# ============================================================
# NODE 4 — GENERATE ACTIVITY
# ============================================================

def generate_activity_node(
    state: TouchGrassState,
    db: Session,
) -> TouchGrassState:

    user_message = state.get(
        "user_message",
        "",
    )

    profile = state.get(
        "profile",
        {},
    )

    history = state.get(
        "history",
        [],
    )

    context = state.get(
        "current_context",
        {},
    )

    prompt = f"""
USER REQUEST:
{user_message}

USER PROFILE:
{json.dumps(
    profile,
    ensure_ascii=False,
    indent=2,
)}

RECENT ACTIVITY HISTORY:
{json.dumps(
    history,
    ensure_ascii=False,
    indent=2,
)}

CURRENT CONTEXT:
{json.dumps(
    context,
    ensure_ascii=False,
    indent=2,
)}

Generate ONE activity.
"""

    try:

        activity = generate_json(
            TOUCHGRASS_PROMPT,
            prompt,
            temperature=0.7,
            max_tokens=600,
        )

        return {
            **state,
            "activity": activity,
            "error": "",
        }

    except Exception as exc:

        return {
            **state,
            "activity": {},
            "error": (
                f"{type(exc).__name__}: {str(exc)}"
            ),
        }


# ============================================================
# NODE 5 — VALIDATE ACTIVITY
# ============================================================

def validate_activity_node(
    state: TouchGrassState,
    db: Session,
) -> TouchGrassState:

    activity = state.get(
        "activity",
        {},
    )

    if not activity:
        return state

    title = str(
        activity.get(
            "title",
            "",
        )
    ).strip()

    description = str(
        activity.get(
            "description",
            "",
        )
    ).strip()

    if not title or not description:
        return {
            **state,
            "error": "Activity generation returned incomplete data.",
        }

    category = str(
        activity.get(
            "category",
            "explore",
        )
    ).lower().strip()

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

    try:

        duration = int(
            activity.get(
                "duration_minutes",
                30,
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        duration = 30

    duration = max(
        5,
        min(duration, 240),
    )

    cleaned = {
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
        "activity": cleaned,
        "error": "",
    }


# ============================================================
# NODE 6 — SAVE ACTIVITY
# ============================================================

def save_activity_node(
    state: TouchGrassState,
    db: Session,
) -> TouchGrassState:

    if state.get("error"):
        return state

    activity_data = state.get(
        "activity",
        {},
    )

    if not activity_data:
        return {
            **state,
            "error": "No activity to save.",
        }

    activity = Activity(
        user_id=state["user_id"],
        title=activity_data["title"],
        description=activity_data["description"],
        category=activity_data["category"],
        duration_minutes=(
            activity_data["duration_minutes"]
        ),
        context=state.get(
            "current_context",
            {},
        ),
        status="suggested",
    )

    db.add(activity)
    db.commit()
    db.refresh(activity)

    saved_activity = {
        **activity_data,
        "id": activity.id,
    }

    return {
        **state,
        "activity": saved_activity,
    }


# ============================================================
# BUILD GRAPH
# ============================================================

def create_touchgrass_graph(
    db: Session,
):

    graph = StateGraph(
        TouchGrassState
    )

    graph.add_node(
        "load_profile",
        lambda state:
            load_profile_node(
                state,
                db,
            ),
    )

    graph.add_node(
        "load_history",
        lambda state:
            load_history_node(
                state,
                db,
            ),
    )

    graph.add_node(
        "build_context",
        lambda state:
            build_context_node(
                state,
                db,
            ),
    )

    graph.add_node(
        "generate_activity",
        lambda state:
            generate_activity_node(
                state,
                db,
            ),
    )

    graph.add_node(
        "validate_activity",
        lambda state:
            validate_activity_node(
                state,
                db,
            ),
    )

    graph.add_node(
        "save_activity",
        lambda state:
            save_activity_node(
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
        "build_context",
    )

    graph.add_edge(
        "build_context",
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


# ============================================================
# RUN GRAPH
# ============================================================

def run_touchgrass_graph(
    user_id: int,
    user_message: str,
    db: Session,
    current_context: dict[str, Any] | None = None,
):

    graph = create_touchgrass_graph(db)

    initial_state: TouchGrassState = {
        "user_id": user_id,
        "user_message": user_message,
        "current_context": (
            current_context or {}
        ),
    }

    return graph.invoke(
        initial_state
    )

