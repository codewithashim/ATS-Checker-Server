from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from beanie import PydanticObjectId
from datetime import timedelta
from typing import Any
from jose import JWTError

from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    create_password_reset_token,
    verify_password_reset_token
)
from app.modules.auth.schemas import (
    UserCreate,
    User,
    UserLogin,
    Token,
    TokenWithUser,
    PasswordReset,
    PasswordResetConfirm,
    EmailVerification,
    UserUpdate
)
from app.modules.auth.models import User as UserModel
from app.modules.auth.services import UserService
from app.modules.shared.queues.email_processing import EmailProcessingQueue

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

# Dependency to get current user
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(token, "access")
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await UserService.get_user_by_id(PydanticObjectId(user_id))
    if user is None:
        raise credentials_exception
    
    return user

async def get_user_by_email(email: str) -> UserModel:
    """Get user by email"""
    return await UserService.get_user_by_email(email)

async def authenticate_user(email: str, password: str) -> UserModel | None:
    """Authenticate user with email and password"""
    user = await get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

@router.post("/signup", response_model=TokenWithUser)
async def signup(user_data: UserCreate):
    """Register a new user"""
    # Check if user already exists
    if await get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password confirmation
    if user_data.password != user_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = await UserService.create_user(user_data, hashed_password)
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user.id), "email": db_user.email},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": str(db_user.id), "email": db_user.email}
    )
    
    # Send verification email
    verification_token = create_password_reset_token(db_user.email)
    await EmailProcessingQueue.add_verification_email_job(db_user.email, verification_token)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user_id": str(db_user.id),
        "name": db_user.name,
        "email": db_user.email,
        "role": db_user.role,
        "is_email_verified": db_user.is_email_verified,
        "created_at": db_user.created_at,
        "updated_at": db_user.updated_at
    }

@router.post("/login", response_model=TokenWithUser)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login user"""
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Update last login
    await UserService.update_last_login(user.id)
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user_id": str(user.id),
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "is_email_verified": user.is_email_verified,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """Refresh access token"""
    try:
        payload = verify_token(refresh_token, "refresh")
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user = await UserService.get_user_by_id(PydanticObjectId(user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        new_refresh_token = create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.post("/logout")
async def logout():
    """Logout user (client should remove tokens)"""
    return {"message": "Successfully logged out"}

@router.post("/forgot-password")
async def forgot_password(data: PasswordReset):
    """Send password reset email"""
    user = await get_user_by_email(data.email)
    if not user:
        # Don't reveal if email exists or not
        return {"message": "If the email exists, a password reset link has been sent"}
    
    reset_token = create_password_reset_token(user.email)
    await EmailProcessingQueue.add_password_reset_email_job(user.email, reset_token)
    
    return {"message": "If the email exists, a password reset link has been sent"}

@router.post("/reset-password")
async def reset_password(data: PasswordResetConfirm):
    """Reset password with token"""
    try:
        email = verify_password_reset_token(data.token)
        user = await get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token"
            )
        
        if data.password != data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )
        
        hashed_password = get_password_hash(data.password)
        await user.update({"$set": {"hashed_password": hashed_password}})
        
        return {"message": "Password reset successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )

@router.post("/verify-email")
async def verify_email(data: EmailVerification):
    """Verify user email"""
    try:
        email = verify_password_reset_token(data.token)
        user = await get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token"
            )
        
        await UserService.verify_email(user.id)
        
        return {"message": "Email verified successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )

@router.post("/resend-verification")
async def resend_verification_email(current_user: User = Depends(get_current_user)):
    """Resend verification email"""
    if current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    verification_token = create_password_reset_token(current_user.email)
    await EmailProcessingQueue.add_verification_email_job(current_user.email, verification_token)
    
    return {"message": "Verification email sent"}

@router.get("/me", response_model=User)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user

@router.put("/me", response_model=User)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update current user profile"""
    updated_user = await UserService.update_user(current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user

@router.delete("/me")
async def delete_current_user(current_user: User = Depends(get_current_user)):
    """Delete current user account"""
    success = await UserService.delete_user(current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return {"message": "User account deleted successfully"}

@router.get("/stats")
async def get_user_stats(current_user: User = Depends(get_current_user)):
    """Get user statistics"""
    stats = await UserService.get_user_stats(current_user.id)
    return stats
