"""Feedback -> long-term memory.

After a user rates an activity, TouchGrass updates their stored profile so the
next recommendation is better:

1. A deterministic step always runs (no AI needed): interests related to the
   activity are strengthened (good rating) or weakened (poor rating).
2. An optional AI step reads the written comment and may add a new interest,
   curiosity, dislike or constraint ("loved searching for unusual plants" ->
   plants). If the AI is unavailable the deterministic step still applies.

The language model is never fine-tuned; only this user's stored memory changes.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from .models import Activity, UserProfile
from .prompts import MEMORY_UPDATE_PROMPT

logger = logging.getLogger("touchgrass.memory")

MAX_LIST_ITEMS = 25
MAX_NOTES = 30
STEP = 0.1


# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------

def _clean_text(value: Any, limit: int = 120) -> str:
    return " ".join(str(value or "").split())[:limit].strip()


def _interest_name(item: Any) -> str:
    """Interests are normally {"name", "strength"}; tolerate older shapes."""
    if isinstance(item, dict):
        return _clean_text(item.get("name") or item.get("raw")).lower()
    return _clean_text(item).lower()


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, round(value, 2)))


def _merge_strings(existing: list | None, additions: Any) -> list[str]:
    result = [str(item) for item in (existing or []) if str(item).strip()]
    seen = {item.lower() for item in result}

    if not isinstance(additions, list):
        return result

    for item in additions:
        text = _clean_text(item)
        if text and text.lower() not in seen:
            result.append(text)
            seen.add(text.lower())

    return result[-MAX_LIST_ITEMS:]


def _related_interests(
    interests: list[dict[str, Any]],
    activity: Activity,
    extra_names: list[str] | None = None,
) -> set[int]:
    """Indexes of interests that this activity touches."""
    haystack = " ".join(
        [
            activity.title or "",
            activity.description or "",
            activity.category or "",
            " ".join(
                (activity.context or {}).get("related_interests", []) or []
            ),
        ]
    ).lower()

    wanted = {name.lower() for name in (extra_names or [])}
    related: set[int] = set()

    for index, item in enumerate(interests):
        name = _interest_name(item)
        if not name:
            continue
        if name in haystack or name in wanted:
            related.add(index)

    return related


# ----------------------------------------------------------------------------
# AI step (best effort)
# ----------------------------------------------------------------------------

def _ask_model_for_changes(
    profile: UserProfile,
    activity: Activity,
    rating: int | None,
    comment: str | None,
    completed: str | None,
) -> dict[str, Any]:
    # Imported lazily so the deterministic step works without the AI module.
    from .ai_service import generate_json

    payload = {
        "activity": {
            "title": activity.title,
            "description": (activity.description or "")[:600],
            "category": activity.category,
            "duration_minutes": activity.duration_minutes,
        },
        "feedback": {
            "rating": rating,
            "completed": completed,
            "comment": comment,
        },
        "current_profile": {
            "interests": [_interest_name(i) for i in (profile.interests or [])],
            "curiosity": profile.curiosity or [],
            "dislikes": profile.dislikes or [],
            "constraints": profile.constraints or [],
        },
    }

    result = generate_json(
        system_prompt=MEMORY_UPDATE_PROMPT,
        user_prompt=json.dumps(payload, ensure_ascii=False),
        temperature=0,
        max_tokens=500,
    )

    return result if isinstance(result, dict) else {}


# ----------------------------------------------------------------------------
# Public entry point
# ----------------------------------------------------------------------------

def apply_feedback_to_profile(
    db: Session,
    user_id: int,
    activity: Activity,
    rating: int | None,
    comment: str | None,
    completed: str | None,
) -> str | None:
    """Update the user's profile from feedback. Returns a short note, or None.

    Never raises: feedback must be saved even if learning fails.
    """

    try:
        profile = (
            db.query(UserProfile)
            .filter(UserProfile.user_id == user_id)
            .first()
        )

        if profile is None:
            return None

        interests = [
            dict(item) if isinstance(item, dict) else {"name": str(item), "strength": 0.5}
            for item in (profile.interests or [])
        ]

        comment = _clean_text(comment, 1000) or None

        # ---- AI step (optional) -------------------------------------------
        changes: dict[str, Any] = {}
        if comment or rating is not None:
            try:
                changes = _ask_model_for_changes(
                    profile, activity, rating, comment, completed
                )
            except Exception as exc:  # noqa: BLE001 - best effort by design
                logger.info("Memory AI step skipped: %s", type(exc).__name__)

        # ---- Deterministic step -------------------------------------------
        boost_names = [
            _clean_text(n).lower()
            for n in (changes.get("boost_interests") or [])
            if isinstance(n, str)
        ]
        reduce_names = [
            _clean_text(n).lower()
            for n in (changes.get("reduce_interests") or [])
            if isinstance(n, str)
        ]

        skipped = (completed or "").lower() in {"no", "skipped", "not_done"}

        if rating is not None and not skipped:
            if rating >= 4:
                for index in _related_interests(interests, activity, boost_names):
                    interests[index]["strength"] = _clamp(
                        float(interests[index].get("strength", 0.5)) + STEP
                    )
            elif rating <= 2:
                for index in _related_interests(interests, activity, reduce_names):
                    interests[index]["strength"] = _clamp(
                        float(interests[index].get("strength", 0.5)) - STEP
                    )

        # New interests the user clearly expressed (e.g. plants).
        known = {_interest_name(i) for i in interests}
        for item in changes.get("add_interests") or []:
            if not isinstance(item, dict):
                continue
            name = _clean_text(item.get("name"), 60).lower()
            if not name or name in known:
                continue
            try:
                strength = _clamp(float(item.get("strength", 0.5)))
            except (TypeError, ValueError):
                strength = 0.5
            # Newly discovered interests start modest; repeat wins grow them.
            interests.append({"name": name, "strength": min(strength, 0.6)})
            known.add(name)

        interests.sort(
            key=lambda i: float(i.get("strength", 0) or 0),
            reverse=True,
        )

        profile.interests = interests[:MAX_LIST_ITEMS]
        profile.curiosity = _merge_strings(
            profile.curiosity, changes.get("add_curiosity")
        )
        profile.dislikes = _merge_strings(
            profile.dislikes, changes.get("add_dislikes")
        )
        profile.constraints = _merge_strings(
            profile.constraints, changes.get("add_constraints")
        )

        # ---- Human-readable memory note -----------------------------------
        note = _clean_text(changes.get("note"), 240)

        if not note:
            if skipped:
                note = f"Did not do '{activity.title}'."
            elif rating is not None and rating >= 4:
                note = f"Enjoyed '{activity.title}'."
            elif rating is not None and rating <= 2:
                note = f"Did not enjoy '{activity.title}'."
            else:
                note = f"Tried '{activity.title}'."

        notes = list(profile.learned_notes or [])
        notes.append(
            {
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "activity": activity.title,
                "rating": rating,
                "note": note,
            }
        )
        profile.learned_notes = notes[-MAX_NOTES:]

        db.commit()
        return note

    except Exception:  # noqa: BLE001
        db.rollback()
        logger.exception("Could not update memory from feedback")
        return None
