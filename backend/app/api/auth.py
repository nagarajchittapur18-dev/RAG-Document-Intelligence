import logging
import re
from fastapi import APIRouter, Depends, HTTPException, status

from app.config import settings
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    UserResponse,
)
from app.services.document_store import DatabaseManager, UserRecord
from app.utils.dependencies import get_current_user
from app.utils.security import create_access_token, hash_password, verify_password

logger = logging.getLogger("ragmate.api.auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])
db = DatabaseManager()

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Creates a new user profile with bcrypt password hashing. Rejects duplicate emails.",
)
async def register(request: RegisterRequest):
    clean_name = request.name.strip()
    clean_email = request.email.strip().lower()

    # Validate name
    if not clean_name or len(clean_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name must be at least 2 non-whitespace characters.",
        )

    # Validate email format
    if not re.match(EMAIL_REGEX, clean_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format.",
        )

    # Validate password length
    if len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long.",
        )

    # Check for existing account
    existing = db.get_user_by_email(clean_email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address is already registered.",
        )

    # Hash password and create user
    hashed_pwd = hash_password(request.password)
    user = db.create_user(
        name=clean_name,
        email=clean_email,
        password_hash=hashed_pwd,
    )

    logger.info("New user registered successfully: %s (ID: %s)", clean_email, user.id)

    return RegisterResponse(
        message="Registration successful",
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            created_at=user.created_at,
        ),
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Authenticate user and receive JWT",
    description="Validates email credentials against bcrypt hash and issues a signed JWT access token.",
)
async def login(request: LoginRequest):
    clean_email = request.email.strip().lower()

    user = db.get_user_by_email(clean_email)
    if not user or not verify_password(request.password, user.password_hash):
        logger.warning("Failed login attempt for email: %s", clean_email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT access token with user.id as subject
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email}
    )

    logger.info("User logged in successfully: %s (ID: %s)", clean_email, user.id)

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRATION_MINUTES * 60,
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            created_at=user.created_at,
        ),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get currently authenticated user",
    description="Returns the profile information of the user identified by the Bearer token.",
)
async def get_me(current_user: UserRecord = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        created_at=current_user.created_at,
    )
