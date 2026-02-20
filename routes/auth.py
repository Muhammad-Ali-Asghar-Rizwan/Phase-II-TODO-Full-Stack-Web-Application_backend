"""Authentication routes for signup and login."""

import re
import bcrypt
from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from models import User
from db import get_session
from jwt_utils import create_access_token
from pydantic import BaseModel, constr
from typing import Optional

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# bcrypt has a 72-byte limit for passwords
MAX_PASSWORD_LENGTH = 72

# Task reference: T026d (Fix bcrypt/passlib compatibility in backend)


# Pydantic models for validation
class UserCreate(BaseModel):
    email: constr(min_length=1, max_length=255)
    password: constr(min_length=8, max_length=MAX_PASSWORD_LENGTH)
    name: Optional[constr(max_length=255)] = None


class UserLogin(BaseModel):
    email: constr(min_length=1, max_length=255)
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    created_at: str


class TokenResponse(BaseModel):
    token: str
    user: UserResponse


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Notes:
    - bcrypt only uses the first 72 bytes of the password. We enforce this limit
      to avoid silent truncation.

    Task reference: T026d (Fix bcrypt/passlib compatibility in backend)
    """
    pw_bytes = password.encode("utf-8")
    if len(pw_bytes) > MAX_PASSWORD_LENGTH:
        raise ValueError(f"Password exceeds maximum length of {MAX_PASSWORD_LENGTH} bytes")

    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash.

    Task reference: T026d (Fix bcrypt/passlib compatibility in backend)
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    """Create a new user account."""
    # Validate email
    if not validate_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )

    # Check if user already exists
    existing_user = (await session.exec(
        select(User).where(User.email == user_data.email)
    )).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    try:
        hashed_password = hash_password(user_data.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        name=user_data.name
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    # Generate JWT token
    token = create_access_token(new_user.id, new_user.email)

    return TokenResponse(
        token=token,
        user=UserResponse(
            id=new_user.id,
            email=new_user.email,
            name=new_user.name,
            created_at=new_user.created_at.isoformat()
        )
    )


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, session: AsyncSession = Depends(get_session)):
    """Login an existing user."""
    # Find user by email
    user = (await session.exec(
        select(User).where(User.email == user_data.email)
    )).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Generate JWT token
    token = create_access_token(user.id, user.email)

    return TokenResponse(
        token=token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at.isoformat()
        )
    )
