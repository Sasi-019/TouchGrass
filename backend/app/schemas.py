from pydantic import BaseModel, EmailStr


# -------------------------
# Authentication schemas
# -------------------------

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# -------------------------
# Profile schemas
# -------------------------

class ProfileCreate(BaseModel):
    interests: list[dict] | None = None
    wants_more_of: list[str] | None = None
    curiosity: list[str] | None = None
    experience_preferences: list[str] | None = None
    dislikes: list[str] | None = None
    constraints: list[str] | None = None
    typical_free_time: str | None = None


class ProfileResponse(BaseModel):
    id: int
    user_id: int
    interests: list[dict] | None = None
    wants_more_of: list[str] | None = None
    curiosity: list[str] | None = None
    experience_preferences: list[str] | None = None
    dislikes: list[str] | None = None
    constraints: list[str] | None = None
    typical_free_time: str | None = None

    class Config:
        from_attributes = True

class ActivityCreate(BaseModel):
    title: str
    description: str
    category: str | None = None
    duration_minutes: int | None = None
    context: dict | None = None


class ActivityResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: str
    category: str | None = None
    duration_minutes: int | None = None
    context: dict | None = None
    status: str

    class Config:
        from_attributes = True


class FeedbackCreate(BaseModel):
    rating: int | None = None
    completed: str | None = None
    comment: str | None = None


class FeedbackResponse(BaseModel):
    id: int
    activity_id: int
    user_id: int
    rating: int | None = None
    completed: str | None = None
    comment: str | None = None

    class Config:
        from_attributes = True        