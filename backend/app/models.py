from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.sql import func

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(
        String,
        nullable=False,
    )

    email = Column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash = Column(
        String,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    interests = Column(
        JSON,
        nullable=True,
    )

    wants_more_of = Column(
        JSON,
        nullable=True,
    )

    curiosity = Column(
        JSON,
        nullable=True,
    )

    experience_preferences = Column(
        JSON,
        nullable=True,
    )

    dislikes = Column(
        JSON,
        nullable=True,
    )

    constraints = Column(
        JSON,
        nullable=True,
    )

    typical_free_time = Column(
        String,
        nullable=True,
    )

    adventure_level = Column(
        String,
        nullable=True,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Short notes the agent writes after feedback, newest last, e.g.
    # {"date": "2026-10-09", "activity": "Nature Texture Hunt",
    #  "rating": 5, "note": "Enjoys close-up observation of plants."}
    # This is the "what TouchGrass has learned about you" memory.
    learned_notes = Column(
        JSON,
        nullable=True,
    )


class Activity(Base):
    __tablename__ = "activities"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    title = Column(
        String,
        nullable=False,
    )

    description = Column(
        Text,
        nullable=False,
    )

    category = Column(
        String,
        nullable=True,
    )

    duration_minutes = Column(
        Integer,
        nullable=True,
    )

    context = Column(
        JSON,
        nullable=True,
    )

    status = Column(
        String,
        nullable=False,
        default="suggested",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class ActivityFeedback(Base):
    __tablename__ = "activity_feedback"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    activity_id = Column(
        Integer,
        ForeignKey("activities.id"),
        nullable=False,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    rating = Column(
        Integer,
        nullable=True,
    )

    completed = Column(
        String,
        nullable=True,
    )

    comment = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class ConversationMessage(Base):
    """
    Stores recent conversations so the TouchGrass agent
    can understand the user's current conversational context.
    """

    __tablename__ = "conversation_messages"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    role = Column(
        String,
        nullable=False,
    )

    content = Column(
        Text,
        nullable=False,
    )

    # The challenge this reply produced (if any), so the chat can show the
    # activity card again after a reload. Nullable => added automatically to
    # existing databases by init_db().
    activity_id = Column(
        Integer,
        ForeignKey("activities.id"),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )