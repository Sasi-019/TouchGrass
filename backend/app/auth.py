from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .config import require_valid_settings
from .database import get_db
from .models import User


settings = require_valid_settings()


# ============================================================
# PASSWORD HASHING (bcrypt)
#
# bcrypt is used directly. The previous passlib wrapper breaks with
# bcrypt >= 4.1 (unpinned in requirements), which makes sign-up fail
# with "password cannot be longer than 72 bytes" on a fresh install.
# Hashes created earlier by passlib ($2b$...) still verify correctly.
# ============================================================

MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")

    if len(password_bytes) > MAX_PASSWORD_BYTES:
        raise ValueError(
            "Password must be at most 72 bytes long."
        )

    return bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(),
    ).decode("utf-8")


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    password_bytes = plain_password.encode("utf-8")

    if len(password_bytes) > MAX_PASSWORD_BYTES:
        return False

    try:
        return bcrypt.checkpw(
            password_bytes,
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        # Malformed stored hash.
        return False


# ============================================================
# JWT
# ============================================================

JWT_SECRET = settings.jwt_secret
JWT_ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def create_access_token(user_id: int) -> str:
    """
    Create a JWT containing the authenticated user's ID.
    """

    expire = (
        datetime.now(timezone.utc)
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return jwt.encode(
        {
            "sub": str(user_id),
            "exp": expire,
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def verify_access_token(token: str) -> int | None:
    """
    Validate a JWT and return the user ID, or None when the
    token is invalid, expired, or has no user ID.
    """

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            return None

        return int(user_id)

    except (JWTError, ValueError, TypeError):
        return None


# ============================================================
# SHARED AUTH DEPENDENCY
#
# One implementation used by every router (it used to be
# copy-pasted into five files). It also confirms the user still
# exists, so a token for a deleted account is rejected with 401
# instead of causing a foreign-key error later.
# ============================================================

# auto_error=False lets us return a clean, consistent 401
# (FastAPI otherwise answers 403 when the header is missing).
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> int:

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Please sign in to continue.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = verify_access_token(credentials.credentials)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Your session has expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    exists = (
        db.query(User.id)
        .filter(User.id == user_id)
        .first()
    )

    if exists is None:
        raise HTTPException(
            status_code=401,
            detail="Account not found. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id
