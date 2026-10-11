from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import (
    create_access_token,
    get_current_user_id,
    hash_password,
    verify_password,
)
from ..database import get_db
from ..models import User
from ..schemas import Token, UserCreate, UserLogin, UserResponse


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


# "/register" is kept as an alias of "/signup" so any client built against the
# original route keeps working.
@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=201,
)
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    include_in_schema=False,
)
def signup(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new TouchGrass account.
    """

    email = _normalize_email(user_data.email)

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists.",
        )

    user = User(
        name=user_data.name.strip(),
        email=email,
        password_hash=hash_password(user_data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post(
    "/login",
    response_model=Token,
)
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Authenticate a user and return a JWT.
    """

    user = (
        db.query(User)
        .filter(User.email == _normalize_email(user_data.email))
        .first()
    )

    # Same message for "no such user" and "wrong password" on purpose.
    if not user or not verify_password(
        user_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    return Token(
        access_token=create_access_token(user.id),
        token_type="bearer",
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Return the currently authenticated user.
    """

    return db.query(User).filter(User.id == user_id).first()
