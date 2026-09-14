"""
Authentication API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    service = AuthService(db)
    existing = await service.get_user_by_username(user_data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{user_data.username}' already exists",
        )
    user = await service.register_user(user_data)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate and return JWT tokens."""
    service = AuthService(db)
    result = await service.authenticate(credentials.username, credentials.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return result


@router.get("/users", response_model=list[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db)):
    """List all users."""
    service = AuthService(db)
    users = await service.list_users()
    return [UserResponse.model_validate(u) for u in users]


@router.post("/seed", response_model=list[UserResponse])
async def seed_users(db: AsyncSession = Depends(get_db)):
    """Seed default users for development."""
    service = AuthService(db)
    users = await service.seed_default_users()
    return [UserResponse.model_validate(u) for u in users]
