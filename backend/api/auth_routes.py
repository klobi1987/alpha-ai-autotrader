"""
Alpha AI Autotrader - Authentication Routes
Login, register, token refresh, and user management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List

from .schemas.auth import (
    UserCreate, UserResponse, UserUpdate,
    LoginRequest, LoginResponse,
    TokenRefreshRequest, TokenRefreshResponse,
    ChangePasswordRequest, MessageResponse
)
from .auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    get_current_superuser
)
from ..models.database import User, get_db
from loguru import logger

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user account

    - **username**: Unique username (3-50 chars, alphanumeric + _ -)
    - **email**: Unique email address
    - **password**: Strong password (min 8 chars, must contain uppercase, lowercase, digit)
    - **full_name**: Optional full name
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = User.hash_password(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"New user registered: {new_user.username} ({new_user.email})")

    return new_user


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with username/email and password

    Returns JWT access token and refresh token
    """
    # Try to find user by username or email
    user = db.query(User).filter(
        (User.username == credentials.username) | (User.email == credentials.username)
    ).first()

    # Check if user exists
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        remaining_minutes = int((user.locked_until - datetime.utcnow()).total_seconds() / 60)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is locked. Try again in {remaining_minutes} minutes."
        )

    # Verify password
    if not user.verify_password(credentials.password):
        # Increment failed login attempts
        user.failed_login_attempts += 1

        # Lock account after 5 failed attempts
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            db.commit()
            logger.warning(f"Account locked due to failed login attempts: {user.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Too many failed login attempts. Account locked for 30 minutes."
            )

        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )

    # Reset failed login attempts on successful login
    user.failed_login_attempts = 0
    user.last_login = datetime.utcnow()
    user.locked_until = None
    db.commit()

    # Create tokens
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})

    logger.info(f"User logged in: {user.username}")

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    token_data: TokenRefreshRequest
):
    """
    Refresh access token using refresh token

    Returns new JWT access token
    """
    try:
        payload = decode_token(token_data.refresh_token)

        # Validate token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        username: str = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        # Create new access token
        access_token = create_access_token(data={"sub": username})

        return TokenRefreshResponse(
            access_token=access_token,
            token_type="bearer"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information

    Requires valid JWT token
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user information

    - **email**: New email address (optional)
    - **full_name**: New full name (optional)
    - **password**: New password (optional)
    """
    # Update email if provided
    if user_update.email and user_update.email != current_user.email:
        # Check if email already exists
        existing_email = db.query(User).filter(
            User.email == user_update.email,
            User.id != current_user.id
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        current_user.email = user_update.email

    # Update full name if provided
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name

    # Update password if provided
    if user_update.password:
        current_user.hashed_password = User.hash_password(user_update.password)

    db.commit()
    db.refresh(current_user)

    logger.info(f"User updated profile: {current_user.username}")

    return current_user


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user password

    - **current_password**: Current password for verification
    - **new_password**: New strong password
    """
    # Verify current password
    if not current_user.verify_password(password_data.current_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect current password"
        )

    # Update password
    current_user.hashed_password = User.hash_password(password_data.new_password)
    db.commit()

    logger.info(f"User changed password: {current_user.username}")

    return MessageResponse(
        message="Password changed successfully",
        success=True
    )


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    List all users (admin only)

    Requires superuser permissions
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    Delete a user (admin only)

    Requires superuser permissions
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent deleting yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    db.delete(user)
    db.commit()

    logger.info(f"User deleted: {user.username} (by {current_user.username})")

    return MessageResponse(
        message=f"User {user.username} deleted successfully",
        success=True
    )
