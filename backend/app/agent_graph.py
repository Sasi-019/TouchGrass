"""TouchGrass LangGraph agent.

Flow (each box is a node, state is passed between them):

    load_profile -> load_conversation -> load_activity_history
        -> build_context          (time, whether a location was shared)
        -> plan                   (LLM decides intent + which tools help;
                                   rule-based fallback if the LLM fails)
        -> execute_tools          (weather / nearby places, never raises)
        -> generate               (Groq writes ONE personalised challenge)
        -> validate               (code checks time, weather, repetition,
                                   dislikes, screen use, invented places)
              |-- problems and attempts left --> generate (with the reasons)
              '-- ok / out of attempts -------> persist
        -> persist                (activity + context + conversation in Postgres)

The LLM proposes; deterministic code verifies. A weak answer is regenerated
instead of being shown to the user.
"""

from __future__ import annotations

import json
import logging
import re
from difflib import SequenceMatcher
from typing import Any, TypedDict

from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from . import real_world_tools as world
from .ai_service import generate_json
from .models import (
    Activity,
    ActivityFeedback,
    ConversationMessage,
    UserProfile,
)
from .prompts import AGENT_SYSTEM_PROMPT, PLANNER_PROMPT

logger = logging.getLogger("touchgrass.agent")

MAX_ATTEMPTS = 3

ALLOWED_INTENTS = {
    "activity", "regenerate", "adapt", "places", "question", "chat",
}
CHALLENGE_INTENTS = {"activity", "regenerate", "adapt", "places"}

ALLOWED_CATEGORIES = {
    "creativity", "outdoors", "learning", "fitness", "social",
    "relaxation", "exploration", "food", "other",
}

# Older prompts used these words; accept them and map to the current set.
CATEGORY_ALIASES = {
    "learn": "learning",
    "create": "creativity",
    "explore": "exploration",
    "move": "fitness",
    "connect": "social",
    "relax": "relaxation",
}


# ============================================================================
# TOOLS (LangChain tools, so they work with LangGraph's ToolNode too)
# ============================================================================

@tool
def weather(
    location: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict:
    """Get current weather and today's forecast for a city or coordinates."""
    return world.get_weather(
        location=location, latitude=latitude, longitude=longitude
    )


@tool
def nearby_places(
    location: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    category: str = "all",
) -> dict:
    """Find real nearby places (parks, cafes, museums, attractions)
    using OpenStreetMap. category: all, parks, cafes, museums, attractions."""
    return world.search_nearby_places(
        location=location,
        latitude=latitude,
        longitude=longitude,
        category=category,
    )


@tool
def current_context(
    timezone_name: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict:
    """Local time, weekday, part of day and whether location is shared."""
    return world.get_current_context(
        timezone_name=timezone_name,
        latitude=latitude,
        longitude=longitude,
    )


@tool
def user_location(
    latitude: float | None = None,
    longitude: float | None = None,
) -> dict:
    """Report whether the user shared their browser location.
    Coordinates are rounded (about 1 km) before being stored."""
    shared = latitude is not None and longitude is not None
    return {
        "shared": shared,
        "approximate_latitude": round(latitude, 2) if shared else None,
        "approximate_longitude": round(longitude, 2) if shared else None,
    }


TOOLS = {
    item.name: item
    for item in (weather, nearby_places, current_context, user_location)
}


def _run_tool(name: str, **arguments: Any) -> dict[str, Any]:
    """Run a tool; a failing tool must never break the conversation."""
    try:
        result = TOOLS[name].invoke(arguments)
        return result if isinstance(result, dict) else {"ok": True, "value": result}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Tool %s failed: %s", name, type(exc).__name__)
        return {"ok": False, "error": f"The {name} tool is unavailable right now."}


# ============================================================================
# STATE
# ============================================================================

class TouchGrassState(TypedDict, total=False):
    user_id: int
    user_message: str
    current_context: dict[str, Any]       # from the request (coords, timezone)

    profile: dict[str, Any]
    conversation_history: list[dict[str, Any]]
    activity_history: list[dict[str, Any]]
    environment: dict[str, Any]           # time + location facts

    plan: dict[str, Any]
    tool_results: list[dict[str, Any]]

    intent: str
    reply: str
    reason: str | None
    activity: dict[str, Any] | None
    weather: dict[str, Any] | None
    nearby_places: list[dict[str, Any]] | None

    attempts: int
    problems: list[str]
    rejected: list[dict[str, Any]]
    validation_notes: list[str]
    error: str


# ============================================================================
# LOADING NODES
# ============================================================================

def _short(text: Any, limit: int) -> str:
    return " ".join(str(text or "").split())[:limit]


def load_profile_node(state: TouchGrassState, db: Session) -> dict:
    profile = (
        db.query(UserProfile)
        .filter(UserProfile.user_id == state["user_id"])
        .first()
    )

    data: dict[str, Any] = {}

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
            # What TouchGrass has learned from the user's feedback.
            "learned_from_feedback": (profile.learned_notes or [])[-8:],
        }

    return {"profile": data}


def load_conversation_node(state: TouchGrassState, db: Session) -> dict:
    messages = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.user_id == state["user_id"])
        .order_by(
            ConversationMessage.created_at.desc(),
            ConversationMessage.id.desc(),
        )
        .limit(8)
        .all()
    )
    messages.reverse()

    return {
        "conversation_history": [
            {"role": item.role, "content": _short(item.content, 500)}
            for item in messages
        ]
    }


def load_activity_history_node(state: TouchGrassState, db: Session) -> dict:
    activities = (
        db.query(Activity)
        .filter(Activity.user_id == state["user_id"])
        .order_by(Activity.created_at.desc(), Activity.id.desc())
        .limit(12)
        .all()
    )

    feedback_by_activity: dict[int, ActivityFeedback] = {}

    if activities:
        rows = (
            db.query(ActivityFeedback)
            .filter(
                ActivityFeedback.user_id == state["user_id"],
                ActivityFeedback.activity_id.in_([a.id for a in activities]),
            )
            .order_by(ActivityFeedback.id.asc())
            .all()
        )
        # Ascending order means the latest feedback wins.
        for row in rows:
            feedback_by_activity[row.activity_id] = row

    history = []

    for item in activities:
        feedback = feedback_by_activity.get(item.id)
        history.append(
            {
                "id": item.id,
                "title": item.title,
                "description": _short(item.description, 220),
                "category": item.category,
                "duration_minutes": item.duration_minutes,
                "status": item.status,
                "rating": feedback.rating if feedback else None,
                "comment": _short(feedback.comment, 200) if feedback and feedback.comment else None,
            }
        )

    return {"activity_history": history}


def build_context_node(state: TouchGrassState) -> dict:
    request = state.get("current_context", {}) or {}

    environment = _run_tool(
        "current_context",
        timezone_name=request.get("timezone"),
        latitude=request.get("latitude"),
        longitude=request.get("longitude"),
    )

    return {"environment": environment}


# ============================================================================
# PLANNING (intent + tools)
# ============================================================================

_MINUTES_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(hours?|hrs?|h|minutes?|mins?|m)\b",
    re.IGNORECASE,
)


def parse_available_minutes(message: str) -> int | None:
    """Pull a stated duration out of text such as '30 minutes' or 'an hour'."""
    text = message.lower()

    if "half an hour" in text or "half hour" in text:
        return 30

    match = _MINUTES_RE.search(text)
    if match:
        amount = float(match.group(1))
        unit = match.group(2).lower()
        minutes = amount * 60 if unit.startswith("h") else amount
        return int(max(5, min(minutes, 600)))

    if re.search(r"\b(an|one)\s+hour\b", text):
        return 60

    return None


def _has(text: str, words: tuple[str, ...]) -> bool:
    """True if any word/phrase appears as whole words ('rain' is not 'train')."""
    return any(
        re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", text)
        for word in words
    )


_PLACE_WORDS = (
    "near me", "nearby", "around me", "close by", "close to me", "park",
    "cafe", "coffee", "museum", "restaurant", "library", "garden", "trail",
    "where can i", "somewhere to go", "place to go",
)
_WEATHER_WORDS = (
    "weather", "raining", "forecast", "temperature", "umbrella",
    "sunny", "how hot", "how cold",
)
_REGEN_WORDS = (
    "another", "something else", "different", "don't like", "do not like",
    "not that", "try again", "next one", "new one", "not feeling",
)
_QUESTION_WORDS = (
    "what do you know", "about me", "my profile", "what have i done",
    "my history", "how does this work", "how do you work", "why did you",
)
_CHAT_WORDS = (
    "hi", "hello", "hey", "thanks", "thank you", "good morning",
    "good evening", "good afternoon",
)
_ADAPT_WORDS = (
    "only have", "tired", "exhausted", "low energy", "too hot", "too cold",
    "indoors", "inside", "with friends", "shorter", "less time", "raining",
)
_OUTDOOR_WORDS = ("outside", "outdoor", "walk", "park", "go out", "hike")


def heuristic_plan(message: str, has_coordinates: bool) -> dict[str, Any]:
    """Rule-based planner used when the LLM planner is unavailable."""
    text = message.lower().strip()
    plain = re.sub(r"[^a-z' ]", "", text).strip()
    words = plain.split()

    is_greeting = bool(words) and len(words) <= 4 and any(
        plain == greeting or plain.startswith(greeting + " ")
        for greeting in _CHAT_WORDS
    )

    if _has(text, _QUESTION_WORDS):
        intent = "question"
    elif _has(text, _REGEN_WORDS):
        intent = "regenerate"
    elif is_greeting:
        intent = "chat"
    elif _has(text, _PLACE_WORDS):
        intent = "places"
    elif _has(text, _WEATHER_WORDS) and not _has(
        text, ("do", "activity", "something")
    ):
        intent = "question"
    elif _has(text, _ADAPT_WORDS):
        intent = "adapt"
    else:
        intent = "activity"

    tools: list[str] = []

    if intent == "places":
        tools = ["nearby_places", "weather"]
    elif _has(text, _WEATHER_WORDS) or (
        intent in CHALLENGE_INTENTS and _has(text, _OUTDOOR_WORDS)
    ):
        tools = ["weather"]

    setting = None
    if _has(text, ("indoors", "inside", "at home")):
        setting = "indoors"
    elif _has(text, ("outdoors", "outside", "outdoor")):
        setting = "outdoors"

    energy = None
    if _has(text, ("tired", "exhausted", "low energy", "no energy")):
        energy = "low"

    social = None
    if _has(text, ("with friends", "with a friend")):
        social = "friends"
    elif _has(text, ("alone", "by myself")):
        social = "solo"

    return {
        "intent": intent,
        "tools": tools,
        "location": None,
        "category": "all",
        "needs_location": bool(tools) and not has_coordinates,
        "available_minutes": None,
        "energy": energy,
        "social": social,
        "setting": setting,
    }


def _normalize_plan(
    raw: Any,
    message: str,
    has_coordinates: bool,
) -> dict[str, Any]:
    plan = heuristic_plan(message, has_coordinates)

    if isinstance(raw, dict):
        intent = raw.get("intent")
        if intent in ALLOWED_INTENTS:
            plan["intent"] = intent

        tools = raw.get("tools")
        if isinstance(tools, list):
            plan["tools"] = [
                name for name in tools if name in {"weather", "nearby_places"}
            ]

        location = raw.get("location")
        if isinstance(location, str) and location.strip():
            plan["location"] = location.strip()[:100]

        if raw.get("category") in {"all", "parks", "cafes", "museums", "attractions"}:
            plan["category"] = raw["category"]

        plan["needs_location"] = bool(raw.get("needs_location", False))

        for key, allowed in (
            ("energy", {"low", "medium", "high"}),
            ("social", {"solo", "friends"}),
            ("setting", {"indoors", "outdoors"}),
        ):
            if raw.get(key) in allowed:
                plan[key] = raw[key]

        minutes = raw.get("available_minutes")
        if isinstance(minutes, (int, float)) and not isinstance(minutes, bool):
            plan["available_minutes"] = int(max(5, min(minutes, 600)))

    # A duration the user literally typed beats a model's reading of it.
    stated = parse_available_minutes(message)
    if stated is not None:
        plan["available_minutes"] = stated

    # Safety net: an outdoor challenge with a known location should check the
    # weather even if the planner forgot to ask for it.
    if (
        has_coordinates
        and plan["intent"] in CHALLENGE_INTENTS
        and plan["setting"] != "indoors"
        and "weather" not in plan["tools"]
    ):
        plan["tools"].append("weather")

    # Places only make sense when the user is asking for somewhere to go.
    if plan["intent"] in {"question", "chat"}:
        plan["tools"] = (
            [t for t in plan["tools"] if t == "weather"]
            if _has(message.lower(), _WEATHER_WORDS)
            else []
        )

    plan["needs_location"] = bool(plan["tools"]) and not (
        has_coordinates or plan["location"]
    )

    return plan


def plan_node(state: TouchGrassState) -> dict:
    request = state.get("current_context", {}) or {}
    has_coordinates = (
        request.get("latitude") is not None
        and request.get("longitude") is not None
    )
    message = state.get("user_message", "")

    planner_input = {
        "recent_conversation": state.get("conversation_history", [])[-6:],
        "current_message": message,
        "location_context": {
            "coordinates_available": has_coordinates,
        },
    }

    raw = None

    try:
        raw = generate_json(
            system_prompt=PLANNER_PROMPT,
            user_prompt=json.dumps(planner_input, ensure_ascii=False),
            temperature=0,
            max_tokens=500,
        )
    except Exception as exc:  # noqa: BLE001
        # Planner failure must not block the user; use the rule-based plan.
        logger.warning("Planner fell back to rules: %s", type(exc).__name__)

    plan = _normalize_plan(raw, message, has_coordinates)

    return {
        "plan": plan,
        "intent": plan["intent"],
        "attempts": 0,
        "rejected": [],
        "problems": [],
        "validation_notes": [],
    }


# ============================================================================
# TOOL EXECUTION
# ============================================================================

def execute_tools_node(state: TouchGrassState) -> dict:
    plan = state.get("plan", {})
    request = state.get("current_context", {}) or {}

    latitude = request.get("latitude")
    longitude = request.get("longitude")
    city = plan.get("location")

    results: list[dict[str, Any]] = []

    if plan.get("tools") and plan.get("needs_location"):
        results.append(
            {
                "tool": "location",
                "ok": False,
                "needs_location": True,
                "error": (
                    "No location is available. Ask the user, once, for a "
                    "city or to tap 'Use my location'."
                ),
            }
        )
        return {"tool_results": results}

    # If the user named a place, that wins over browser coordinates.
    where = (
        {"location": city}
        if city
        else {"latitude": latitude, "longitude": longitude}
    )

    for name in plan.get("tools", []):
        if name == "weather":
            result = _run_tool("weather", **where)
        elif name == "nearby_places":
            result = _run_tool(
                "nearby_places",
                category=plan.get("category", "all"),
                **where,
            )
        else:
            continue

        results.append({"tool": name, **result})

    return {"tool_results": results}


# ============================================================================
# GENERATION
# ============================================================================

def _compact_tool_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compact = []

    for item in results:
        if item.get("tool") == "weather" and item.get("ok"):
            compact.append(
                {
                    "tool": "weather",
                    "location": item.get("location"),
                    "summary": item.get("summary"),
                    "outdoor_ok": item.get("outdoor_ok"),
                    "is_wet": item.get("is_wet"),
                }
            )
        elif item.get("tool") == "nearby_places" and item.get("ok"):
            compact.append(
                {
                    "tool": "nearby_places",
                    "search_area": item.get("search_area"),
                    "note": item.get("note"),
                    "places": [
                        {
                            "name": place.get("name"),
                            "type": place.get("type"),
                            "distance_m": place.get("distance_m"),
                            "opening_hours": place.get("opening_hours"),
                        }
                        for place in (item.get("places") or [])[:10]
                    ],
                }
            )
        else:
            compact.append(item)

    return compact


def generate_node(state: TouchGrassState) -> dict:
    plan = state.get("plan", {})
    history = state.get("activity_history", [])
    intent = state.get("intent", "activity")

    previous = next(
        (
            item
            for item in history
            if item.get("status") == "suggested"
        ),
        None,
    )

    context = {
        "intent": intent,
        "latest_user_message": state.get("user_message", ""),
        "user_profile": state.get("profile", {}),
        "recent_conversation": state.get("conversation_history", []),
        "recent_activities": [
            {k: v for k, v in item.items() if k != "id"}
            for item in history
        ],
        "recently_suggested_titles": [item["title"] for item in history],
        "current_context": {
            **state.get("environment", {}),
            "available_minutes": plan.get("available_minutes"),
            "energy": plan.get("energy"),
            "social": plan.get("social"),
            "setting": plan.get("setting"),
        },
        "tool_results": _compact_tool_results(state.get("tool_results", [])),
    }

    if intent in {"regenerate", "adapt"} and previous:
        context["activity_to_replace"] = {
            "title": previous["title"],
            "description": previous["description"],
        }

    if state.get("rejected"):
        context["rejected_attempts_this_turn"] = state["rejected"]

    prompt = (
        "Respond to the latest user message using the context below.\n\n"
        + json.dumps(context, ensure_ascii=False, indent=1)
    )

    result = generate_json(
        system_prompt=AGENT_SYSTEM_PROMPT,
        user_prompt=prompt,
        temperature=0.6,
        max_tokens=1400,
    )

    if not isinstance(result, dict):
        result = {}

    return {
        "reply": result.get("reply") or "",
        "reason": result.get("reason"),
        "activity": result.get("activity"),
        # The planner's intent is authoritative; the model only chooses between
        # chat / clarify when no challenge is needed.
        "intent": (
            intent
            if intent in CHALLENGE_INTENTS
            else (result.get("intent") if result.get("intent") in {"chat", "clarify"} else "chat")
        ),
        "attempts": state.get("attempts", 0) + 1,
    }


# ============================================================================
# VALIDATION (deterministic checks on the model's proposal)
# ============================================================================

_SCREEN_PATTERNS = (
    r"\bscroll", r"social media", r"\bstream", r"watch (a|an|some|the) "
    r"(video|movie|show|series|film)", r"\bplay (a )?(video )?game",
    r"\bbrowse (the )?(internet|web)", r"\bdoom",
)
_UNSAFE_PATTERNS = (
    r"trespass", r"\billegal", r"break into", r"climb (a|the) fence",
    r"swim alone", r"\bdrunk\b", r"walk alone (at|in the) (night|dark)",
)
_NEGATION_WINDOW = re.compile(
    r"(avoid|away from|without|no|not|skip|instead of)\W+(\w+\W+){0,3}$"
)


def _normalise_title(title: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()


def _too_similar(a: str, b: str) -> bool:
    a, b = _normalise_title(a), _normalise_title(b)

    if not a or not b:
        return False
    if a == b:
        return True
    if SequenceMatcher(None, a, b).ratio() >= 0.82:
        return True

    tokens_a, tokens_b = set(a.split()), set(b.split())
    if len(tokens_a) >= 2 and len(tokens_b) >= 2:
        overlap = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
        return overlap >= 0.75

    return False


def _dislike_phrases(dislikes: list[Any]) -> list[str]:
    phrases: list[str] = []

    for item in dislikes or []:
        for piece in re.split(r",|;|\band\b|\bor\b", str(item).lower()):
            piece = piece.strip(" .")
            if len(piece) >= 4:
                phrases.append(piece)

    return phrases


def _mentions_without_negation(text: str, phrase: str) -> bool:
    start = 0
    while True:
        index = text.find(phrase, start)
        if index == -1:
            return False
        if not _NEGATION_WINDOW.search(text[:index]):
            return True
        start = index + len(phrase)


def validate_candidate(
    raw: Any,
    *,
    plan: dict[str, Any],
    profile: dict[str, Any],
    history: list[dict[str, Any]],
    environment: dict[str, Any],
    tool_results: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, list[str], list[str]]:
    """Check one proposed activity.

    Returns (cleaned_activity, problems, notes).
    ``problems`` force a retry; ``notes`` are harmless auto-fixes.
    """

    problems: list[str] = []
    notes: list[str] = []

    if not isinstance(raw, dict):
        return None, ["No activity object was produced."], notes

    title = _short(raw.get("title"), 200)
    description = " ".join(str(raw.get("description") or "").split())[:3000]

    if not title:
        problems.append("The activity needs a specific title.")
    if not description:
        problems.append("The activity needs clear step-by-step instructions.")
    if problems:
        return None, problems, notes

    # ---- category -----------------------------------------------------------
    category = str(raw.get("category") or "other").strip().lower()
    category = CATEGORY_ALIASES.get(category, category)
    if category not in ALLOWED_CATEGORIES:
        category = "other"

    # ---- duration vs. time available ------------------------------------------
    try:
        duration = int(raw.get("duration_minutes"))
    except (TypeError, ValueError):
        duration = None

    if duration is not None:
        duration = max(5, min(duration, 240))

    available = plan.get("available_minutes")

    if available and duration and duration > available:
        problems.append(
            f"It takes {duration} minutes but the user only has {available}. "
            f"Choose something that fits within {available} minutes in total, "
            "including any travel."
        )

    # ---- location type / weather / time of day --------------------------------
    location_type = str(raw.get("location_type") or "either").lower()
    if location_type not in {"outdoors", "indoors", "either"}:
        location_type = "either"

    weather_result = next(
        (r for r in tool_results if r.get("tool") == "weather" and r.get("ok")),
        None,
    )

    if location_type == "outdoors":
        if weather_result and weather_result.get("outdoor_ok") is False:
            problems.append(
                "The weather is unsuitable for outdoor activity "
                f"({weather_result.get('summary')}). Suggest an indoor "
                "or sheltered idea."
            )
        if environment.get("part_of_day") == "night":
            problems.append(
                "It is night time. Suggest an indoor or very safe nearby idea."
            )
        if plan.get("setting") == "indoors":
            problems.append("The user asked to stay indoors.")

    if plan.get("setting") == "outdoors" and location_type == "indoors":
        problems.append("The user asked for something outdoors.")

    # ---- energy / difficulty -----------------------------------------------------
    difficulty = str(raw.get("difficulty") or "moderate").lower()
    if difficulty not in {"easy", "moderate", "challenging"}:
        difficulty = "moderate"

    if plan.get("energy") == "low" and (
        difficulty == "challenging" or category == "fitness"
    ):
        problems.append(
            "The user is low on energy. Choose something gentle and easy."
        )

    # ---- screen use ----------------------------------------------------------------
    screen_use = str(raw.get("screen_use") or "low").lower()
    if screen_use not in {"none", "low"}:
        problems.append(
            "The activity relies too much on a screen. It must be mostly offline."
        )
        screen_use = "low"

    body = f"{title} {description}".lower()

    if any(re.search(pattern, body) for pattern in _SCREEN_PATTERNS):
        problems.append(
            "The instructions centre on screen use. Replace them with a "
            "hands-on, offline activity."
        )

    if any(re.search(pattern, body) for pattern in _UNSAFE_PATTERNS):
        problems.append("The activity is unsafe or potentially illegal.")

    # ---- dislikes ----------------------------------------------------------------------
    for phrase in _dislike_phrases(profile.get("dislikes", [])):
        if _mentions_without_negation(body, phrase):
            problems.append(
                f"The user dislikes '{phrase}'. Do not include it."
            )
            break

    # ---- repetition ----------------------------------------------------------------------
    # (Titles rejected earlier in this same turn are passed to the model in
    # the prompt; they are not "history", so they are not compared here.)
    seen_titles = [item.get("title", "") for item in history]

    for old_title in seen_titles:
        if _too_similar(title, old_title):
            problems.append(
                f"'{title}' is too similar to a recent activity "
                f"('{old_title}'). Propose something clearly different."
            )
            break

    # ---- place must come from tool results (never invented) --------------------
    place = raw.get("place")
    verified_place = None

    if isinstance(place, dict) and place.get("name"):
        places_result = next(
            (
                r for r in tool_results
                if r.get("tool") == "nearby_places" and r.get("ok")
            ),
            None,
        )
        known = {
            str(p.get("name", "")).casefold(): p
            for p in (places_result or {}).get("places", [])
        }
        match = known.get(str(place["name"]).casefold())

        if match:
            verified_place = {
                "name": match["name"],
                "type": match.get("type"),
                "distance_m": match.get("distance_m"),
                "latitude": match.get("latitude"),
                "longitude": match.get("longitude"),
            }
        else:
            notes.append(
                f"Removed unverified place '{place.get('name')}'."
            )

    related = raw.get("related_interests")
    related = (
        [_short(item, 60) for item in related[:6]]
        if isinstance(related, list)
        else []
    )

    cleaned = {
        "title": title,
        "description": description,
        "category": category,
        "duration_minutes": duration,
        "location_type": location_type,
        "screen_use": screen_use,
        "difficulty": difficulty,
        "related_interests": related,
        "place": verified_place,
        "reason": _short(raw.get("reason"), 1000),
    }

    return cleaned, problems, notes


def validate_node(state: TouchGrassState) -> dict:
    intent = state.get("intent", "chat")

    if intent not in CHALLENGE_INTENTS:
        return {"activity": None, "problems": []}

    cleaned, problems, notes = validate_candidate(
        state.get("activity"),
        plan=state.get("plan", {}),
        profile=state.get("profile", {}),
        history=state.get("activity_history", []),
        environment=state.get("environment", {}),
        tool_results=state.get("tool_results", []),
        rejected=state.get("rejected", []),
    )

    rejected = list(state.get("rejected", []))

    if problems:
        title = (
            (state.get("activity") or {}).get("title")
            if isinstance(state.get("activity"), dict)
            else None
        )
        rejected.append({"title": title or "", "problems": problems})

    return {
        "activity": cleaned,
        "problems": problems,
        "rejected": rejected,
        "validation_notes": list(state.get("validation_notes", [])) + notes,
    }


def route_after_validate(state: TouchGrassState) -> str:
    if (
        state.get("problems")
        and state.get("attempts", 0) < MAX_ATTEMPTS
    ):
        return "generate"

    return "finalize"


def finalize_node(state: TouchGrassState) -> dict:
    """Turn the validated state into the reply the user will see."""

    intent = state.get("intent", "chat")
    reply = (state.get("reply") or "").strip()
    reason = state.get("reason")
    activity = state.get("activity")

    # Challenge intents still failing validation after every attempt:
    # ask for information instead of showing something unsuitable.
    if intent in CHALLENGE_INTENTS and (state.get("problems") or not activity):
        return {
            "intent": "clarify",
            "reply": (
                "I couldn't find something that fits well right now. "
                "Tell me how much time you have, whether you'd like to be "
                "indoors or outdoors, and (optionally) tap 'Use my location' "
                "so I can check the weather and nearby places."
            ),
            "reason": None,
            "activity": None,
        }

    if intent in CHALLENGE_INTENTS and not reply:
        reply = "Here's one challenge for you. Then put your phone away."

    if intent not in CHALLENGE_INTENTS:
        activity = None

    if not reply:
        reply = "I'm here. What would you like to do?"

    weather_result = next(
        (r for r in state.get("tool_results", []) if r.get("tool") == "weather" and r.get("ok")),
        None,
    )
    places_result = next(
        (r for r in state.get("tool_results", []) if r.get("tool") == "nearby_places" and r.get("ok")),
        None,
    )

    return {
        "reply": reply,
        "reason": reason or (activity or {}).get("reason"),
        "activity": activity,
        "weather": (
            {
                "location": weather_result.get("location"),
                "summary": weather_result.get("summary"),
                "outdoor_ok": weather_result.get("outdoor_ok"),
            }
            if weather_result
            else None
        ),
        "nearby_places": (
            [
                {
                    "name": p.get("name"),
                    "type": p.get("type"),
                    "distance_m": p.get("distance_m"),
                    "address": p.get("address"),
                }
                for p in (places_result.get("places") or [])[:8]
            ]
            if places_result
            else None
        ),
    }


# ============================================================================
# PERSISTENCE
# ============================================================================

def persist_node(state: TouchGrassState, db: Session) -> dict:
    try:
        saved_activity = None
        activity = state.get("activity")

        if state.get("intent") in CHALLENGE_INTENTS and activity:
            request = state.get("current_context", {}) or {}
            environment = dict(state.get("environment", {}))

            # A rejected suggestion becomes "skipped" so history stays honest.
            if state.get("intent") == "regenerate":
                previous = next(
                    (
                        item
                        for item in state.get("activity_history", [])
                        if item.get("status") == "suggested"
                    ),
                    None,
                )
                if previous:
                    db.query(Activity).filter(
                        Activity.id == previous["id"],
                        Activity.user_id == state["user_id"],
                    ).update({"status": "skipped"})

            latitude = request.get("latitude")
            longitude = request.get("longitude")

            record = Activity(
                user_id=state["user_id"],
                title=activity["title"],
                description=activity["description"],
                category=activity.get("category"),
                duration_minutes=activity.get("duration_minutes"),
                context={
                    "request": state.get("user_message", ""),
                    "intent": state.get("intent"),
                    "reason": activity.get("reason"),
                    "location_type": activity.get("location_type"),
                    "screen_use": activity.get("screen_use"),
                    "difficulty": activity.get("difficulty"),
                    "related_interests": activity.get("related_interests", []),
                    "place": activity.get("place"),
                    "environment": environment,
                    "stated": {
                        "available_minutes": state.get("plan", {}).get("available_minutes"),
                        "energy": state.get("plan", {}).get("energy"),
                        "social": state.get("plan", {}).get("social"),
                        "setting": state.get("plan", {}).get("setting"),
                    },
                    "weather": (state.get("weather") or {}).get("summary"),
                    # Coordinates are rounded (~1 km) before being stored.
                    "approximate_location": (
                        {
                            "latitude": round(latitude, 2),
                            "longitude": round(longitude, 2),
                        }
                        if latitude is not None and longitude is not None
                        else None
                    ),
                    "tools_used": [
                        item.get("tool")
                        for item in state.get("tool_results", [])
                        if item.get("ok")
                    ],
                    "attempts": state.get("attempts", 1),
                    "validation_notes": state.get("validation_notes", []),
                },
                status="suggested",
            )
            db.add(record)
            db.flush()
            saved_activity = {**activity, "id": record.id}

        db.add_all(
            [
                ConversationMessage(
                    user_id=state["user_id"],
                    role="user",
                    content=state["user_message"],
                ),
                ConversationMessage(
                    user_id=state["user_id"],
                    role="assistant",
                    content=state["reply"],
                    activity_id=(
                        saved_activity["id"] if saved_activity else None
                    ),
                ),
            ]
        )
        db.commit()

        return {"activity": saved_activity, "error": ""}

    except Exception:
        db.rollback()
        raise


# ============================================================================
# GRAPH
# ============================================================================

def create_touchgrass_graph(db: Session):
    graph = StateGraph(TouchGrassState)

    graph.add_node("load_profile", lambda s: load_profile_node(s, db))
    graph.add_node("load_conversation", lambda s: load_conversation_node(s, db))
    graph.add_node(
        "load_activity_history", lambda s: load_activity_history_node(s, db)
    )
    graph.add_node("build_context", build_context_node)
    graph.add_node("plan", plan_node)
    graph.add_node("execute_tools", execute_tools_node)
    graph.add_node("generate", generate_node)
    graph.add_node("validate", validate_node)
    graph.add_node("finalize", finalize_node)
    graph.add_node("persist", lambda s: persist_node(s, db))

    graph.add_edge(START, "load_profile")
    graph.add_edge("load_profile", "load_conversation")
    graph.add_edge("load_conversation", "load_activity_history")
    graph.add_edge("load_activity_history", "build_context")
    graph.add_edge("build_context", "plan")
    graph.add_edge("plan", "execute_tools")
    graph.add_edge("execute_tools", "generate")
    graph.add_edge("generate", "validate")

    # Invalid proposal -> regenerate with the reasons; otherwise finish.
    graph.add_conditional_edges(
        "validate",
        route_after_validate,
        {"generate": "generate", "finalize": "finalize"},
    )

    graph.add_edge("finalize", "persist")
    graph.add_edge("persist", END)

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
