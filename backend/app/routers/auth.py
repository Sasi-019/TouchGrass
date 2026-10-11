from fastapi import APIRouter, Depends, HTTPException
<<<<<<< HEAD
=======
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
from sqlalchemy.orm import Session

from ..auth import (
    create_access_token,
<<<<<<< HEAD
    get_current_user_id,
    hash_password,
=======
    hash_password,
    verify_access_token,
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
    verify_password,
)
from ..database import get_db
from ..models import User
from ..schemas import Token, UserCreate, UserLogin, UserResponse


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

<<<<<<< HEAD

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
=======
security = HTTPBearer()


@router.post(
    "/signup",
    response_model=UserResponse,
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
)
def signup(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new TouchGrass account.
    """

<<<<<<< HEAD
    email = _normalize_email(user_data.email)

    existing_user = (
        db.query(User)
        .filter(User.email == email)
=======
    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
<<<<<<< HEAD
            detail="An account with this email already exists.",
=======
            detail="An account with this email already exists",
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
        )

    user = User(
        name=user_data.name.strip(),
<<<<<<< HEAD
        email=email,
        password_hash=hash_password(user_data.password),
=======
        email=user_data.email,
        password_hash=hash_password(
            user_data.password
        ),
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
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
<<<<<<< HEAD
        .filter(User.email == _normalize_email(user_data.email))
        .first()
    )

    # Same message for "no such user" and "wrong password" on purpose.
=======
        .filter(User.email == user_data.email)
        .first()
    )

>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
    if not user or not verify_password(
        user_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
<<<<<<< HEAD
            detail="Invalid email or password.",
        )

    return Token(
        access_token=create_access_token(user.id),
=======
            detail="Invalid email or password",
        )

    token = create_access_token(user.id)

    return Token(
        access_token=token,
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
        token_type="bearer",
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_current_user(
<<<<<<< HEAD
    user_id: int = Depends(get_current_user_id),
=======
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
    db: Session = Depends(get_db),
):
    """
    Return the currently authenticated user.
    """

<<<<<<< HEAD
    return db.query(User).filter(User.id == user_id).first()
=======
    user_id = verify_access_token(
        credentials.credentials
    )

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token",
        )

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return user
>>>>>>> 086f3d78cf4b16b3a4c49d79dcb806f55d124191
