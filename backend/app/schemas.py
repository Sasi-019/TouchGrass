from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ============================================================
# AUTHENTICATION
# ============================================================

class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


# ============================================================
# PROFILE
# ============================================================

class ProfileCreate(BaseModel):
    interests: list[dict[str, Any]] | None = None
    wants_more_of: list[str] | None = None
    curiosity: list[str] | None = None
    experience_preferences: list[str] | None = None
    dislikes: list[str] | None = None
    constraints: list[str] | None = None
    typical_free_time: str | None = None
    adventure_level: str | None = None


class ProfileResponse(BaseModel):
    id: int
    user_id: int

    interests: list[dict[str, Any]] | None = None
    wants_more_of: list[str] | None = None
    curiosity: list[str] | None = None
    experience_preferences: list[str] | None = None
    dislikes: list[str] | None = None
    constraints: list[str] | None = None
    typical_free_time: str | None = None
    adventure_level: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# ACTIVITY
# ============================================================

class ActivityCreate(BaseModel):
    title: str
    description: str
    category: str | None = None
    duration_minutes: int | None = None
    context: dict[str, Any] | None = None


class ActivityResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: str
    category: str | None = None
    duration_minutes: int | None = None
    context: dict[str, Any] | None = None
    status: str

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# FEEDBACK
# ============================================================

class FeedbackCreate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    completed: str | None = None
    comment: str | None = Field(default=None, max_length=1000)


class FeedbackResponse(BaseModel):
    id: int
    activity_id: int
    user_id: int
    rating: int | None = None
    completed: str | None = None
    comment: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# AGENT / CHAT
# ============================================================

class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

    # Location is optional.
    # The frontend sends these only when the user has granted
    # browser location permission.
    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    # Allows the frontend to tell the backend whether
    # the user currently wants voice-oriented behavior.
    voice_enabled: bool = False


class AgentActivity(BaseModel):
    title: str
    description: str
    category: str | None = None
    duration_minutes: int | None = None
    reason: str | None = None


class AgentChatResponse(BaseModel):
    message: str
    intent: str | None = None
    activity_id: int | None = None
    activity: AgentActivity | None = None
    reason: str | None = None
    weather: dict[str, Any] | None = None
    nearby_places: list[dict[str, Any]] | None = None


# ============================================================
# VOICE
# ============================================================

class VoiceTranscriptionResponse(BaseModel):
    text: str
    model: str      