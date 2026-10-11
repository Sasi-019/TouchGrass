<<<<<<< HEAD
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..agent_graph import run_touchgrass_graph
from ..ai_service import AIServiceError
from ..auth import get_current_user_id
from ..database import get_db
from ..models import Activity, ConversationMessage
=======

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..agent_graph import run_touchgrass_graph
from ..auth import verify_access_token
from ..database import get_db
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
from ..schemas import (
    AgentActivity,
    AgentChatRequest,
    AgentChatResponse,
<<<<<<< HEAD
    ChatHistoryActivity,
    ChatHistoryMessage,
)

logger = logging.getLogger("touchgrass.agent")

=======
)

>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
router = APIRouter(
    prefix="/agent",
    tags=["Agent"],
)

<<<<<<< HEAD
=======
security = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    user_id = verify_access_token(credentials.credentials)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )

    return user_id

>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191

@router.post(
    "/chat",
    response_model=AgentChatResponse,
)
def agent_chat(
    payload: AgentChatRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
<<<<<<< HEAD
    # Location is optional. When the user has not granted it the agent
    # still works; it just can't check weather or nearby places by itself.
    context = {
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "timezone": payload.timezone,
=======
    context = {
        "latitude": payload.latitude,
        "longitude": payload.longitude,
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
        "voice_enabled": payload.voice_enabled,
    }

    try:
        result = run_touchgrass_graph(
            user_id=user_id,
            user_message=payload.message,
            db=db,
            current_context=context,
        )

<<<<<<< HEAD
    except AIServiceError as exc:
        logger.warning("AI service error: %s", exc)

        raise HTTPException(
            status_code=502,
            detail=(
                "TouchGrass's AI is unavailable right now. "
                "Please try again in a moment."
            ),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:  # noqa: BLE001
        logger.exception("Agent graph failed")

        raise HTTPException(
            status_code=500,
            detail="Something went wrong while thinking. Please try again.",
        ) from exc

    activity = result.get("activity")
=======
    except Exception as exc:
        print("\n========== LANGGRAPH ERROR ==========")
        print(type(exc).__name__, str(exc))
        print("=====================================\n")

        raise HTTPException(
            status_code=500,
            detail=f"LangGraph failed: {type(exc).__name__}: {str(exc)}",
        ) from exc

    if result.get("error"):
        print("\n========== AGENT GRAPH ERROR ==========")
        print(result["error"])
        print("========================================\n")

        raise HTTPException(
            status_code=500,
            detail=str(result["error"]),
        )

    activity = result.get("activity")
    intent = result.get("intent", "chat")
    reply = result.get(
        "reply",
        "I'm here. What would you like to explore?",
    )
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191

    response_activity = None

    if activity:
        response_activity = AgentActivity(
            title=activity["title"],
            description=activity["description"],
            category=activity.get("category"),
            duration_minutes=activity.get("duration_minutes"),
            reason=activity.get("reason"),
<<<<<<< HEAD
            location_type=activity.get("location_type"),
            difficulty=activity.get("difficulty"),
            related_interests=activity.get("related_interests"),
            place=activity.get("place"),
        )

    needs_location = any(
        item.get("needs_location")
        for item in (result.get("tool_results") or [])
    )

    return AgentChatResponse(
        message=result.get("reply")
        or "I'm here. What would you like to explore?",
        needs_location=needs_location,
        intent=result.get("intent", "chat"),
        activity_id=activity.get("id") if activity else None,
        activity=response_activity,
        reason=result.get("reason"),
        weather=result.get("weather"),
        nearby_places=result.get("nearby_places"),
    )


@router.get(
    "/history",
    response_model=list[ChatHistoryMessage],
)
def chat_history(
    limit: int = 60,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """The user's recent conversation, oldest first, so the chat screen can
    show it again after a reload or on another device."""

    limit = max(1, min(limit, 200))

    messages = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.user_id == user_id)
        .order_by(
            ConversationMessage.created_at.desc(),
            ConversationMessage.id.desc(),
        )
        .limit(limit)
        .all()
    )
    messages.reverse()

    activity_ids = {m.activity_id for m in messages if m.activity_id}
    activities = {}

    if activity_ids:
        # Scoped to this user: one user can never read another's activities.
        activities = {
            a.id: a
            for a in db.query(Activity)
            .filter(Activity.id.in_(activity_ids), Activity.user_id == user_id)
            .all()
        }

    return [
        ChatHistoryMessage(
            id=m.id,
            role=m.role,
            content=m.content,
            created_at=m.created_at.isoformat() if m.created_at else None,
            activity=(
                ChatHistoryActivity.model_validate(activities[m.activity_id])
                if m.activity_id in activities
                else None
            ),
        )
        for m in messages
    ]


@router.delete("/history")
def clear_chat_history(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Start a fresh conversation. Activities and feedback are kept."""

    deleted = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.user_id == user_id)
        .delete(synchronize_session=False)
    )
    db.commit()

    return {"message": "Conversation cleared.", "deleted": deleted}
=======
        )

    return AgentChatResponse(
        message=reply,
        intent=intent,
        activity_id=activity.get("id") if activity else None,
        activity=response_activity,
        reason=result.get("reason"),
        weather=None,
        nearby_places=None,
    )

>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
