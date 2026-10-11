from typing import Any

<<<<<<< HEAD
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
=======
from pydantic import BaseModel, ConfigDict, EmailStr, Field
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191


# ============================================================
# AUTHENTICATION
# ============================================================

class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
<<<<<<< HEAD
    password: str = Field(min_length=8, max_length=72)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Name cannot be blank.")

        return value

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        # bcrypt only uses the first 72 BYTES (emoji/accents use several).
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password is too long (max 72 bytes).")

        return value
=======
    password: str = Field(min_length=6, max_length=128)
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191


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

<<<<<<< HEAD
    # What TouchGrass has learned from the user's feedback (read-only).
    learned_notes: list[dict[str, Any]] | None = None

=======
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
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

<<<<<<< HEAD
    # Short sentence describing what TouchGrass learned from this feedback.
    memory_note: str | None = None

=======
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
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

<<<<<<< HEAD
    # IANA timezone from the browser (e.g. "Asia/Kolkata"), so "morning"
    # and "after dark" are judged in the user's time, not the server's.
    timezone: str | None = Field(default=None, max_length=64)

=======
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
    # Allows the frontend to tell the backend whether
    # the user currently wants voice-oriented behavior.
    voice_enabled: bool = False


class AgentActivity(BaseModel):
    title: str
    description: str
    category: str | None = None
    duration_minutes: int | None = None
    reason: str | None = None
<<<<<<< HEAD
    location_type: str | None = None
    difficulty: str | None = None
    related_interests: list[str] | None = None
    place: dict[str, Any] | None = None
=======
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191


class AgentChatResponse(BaseModel):
    message: str
<<<<<<< HEAD
    # True when a tool (weather / nearby places) was wanted but no location
    # was available, so the UI can offer a one-tap "Use my location".
    needs_location: bool = False
=======
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
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
<<<<<<< HEAD
    model: str      

# ============================================================
# CHAT HISTORY
# ============================================================

class ChatHistoryActivity(BaseModel):
    id: int
    title: str
    description: str
    category: str | None = None
    duration_minutes: int | None = None
    status: str
    context: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)


class ChatHistoryMessage(BaseModel):
    id: int
    role: str
    content: str
    created_at: str | None = None
    activity: ChatHistoryActivity | None = None
=======
    model: str      
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
