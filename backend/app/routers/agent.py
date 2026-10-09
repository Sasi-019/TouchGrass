
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..agent_graph import run_touchgrass_graph
from ..auth import verify_access_token
from ..database import get_db
from ..schemas import (
    AgentActivity,
    AgentChatRequest,
    AgentChatResponse,
)

router = APIRouter(
    prefix="/agent",
    tags=["Agent"],
)

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


@router.post(
    "/chat",
    response_model=AgentChatResponse,
)
def agent_chat(
    payload: AgentChatRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    context = {
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "voice_enabled": payload.voice_enabled,
    }

    try:
        result = run_touchgrass_graph(
            user_id=user_id,
            user_message=payload.message,
            db=db,
            current_context=context,
        )

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

    response_activity = None

    if activity:
        response_activity = AgentActivity(
            title=activity["title"],
            description=activity["description"],
            category=activity.get("category"),
            duration_minutes=activity.get("duration_minutes"),
            reason=activity.get("reason"),
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

