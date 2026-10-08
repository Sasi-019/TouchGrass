from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import verify_access_token
from ..agent_service import build_agent


router = APIRouter(prefix="/agent", tags=["Agent"])

security = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user_id = verify_access_token(credentials.credentials)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    return user_id


@router.post("/chat")
def agent_chat(
    message: dict,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user_message = message.get("message", "").strip()

    if not user_message:
        raise HTTPException(
            status_code=400,
            detail="Message is required",
        )

    state = {
        "user_id": user_id,
        "user_message": user_message,
    }

    agent = build_agent(db)

    result = agent.invoke(state)

    return {
        "message": user_message,
        "intent": result.get("intent"),
        "activity_id": result.get("activity_id"),
        "activity": result.get("activity"),
        "reason": result.get("response"),
    }