"""
Authentication service — JWT token management, user registration, and login.
"""

import hashlib
import logging
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import Role, User
from app.schemas.auth import TokenResponse, UserCreate, UserResponse

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthService:
    """Handles authentication, token generation, and user management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Password Hashing ─────────────────────────────────────────
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using PBKDF2-SHA256 with random salt."""
        import secrets
        salt = secrets.token_hex(16)
        hash_val = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
        return f"{salt}${hash_val.hex()}"

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against stored hash."""
        try:
            salt, stored_hash = hashed_password.split("$", 1)
            computed = hashlib.pbkdf2_hmac("sha256", plain_password.encode(), salt.encode(), 100_000)
            return computed.hex() == stored_hash
        except (ValueError, AttributeError):
            return False

    # ── Token Generation ─────────────────────────────────────────
    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
        )
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    @staticmethod
    def create_refresh_token(data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    @staticmethod
    def decode_token(token: str) -> dict | None:
        try:
            payload = jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )
            return payload
        except JWTError:
            return None

    # ── User Operations ──────────────────────────────────────────
    async def register_user(self, user_data: UserCreate) -> User:
        """Register a new user."""
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=self.hash_password(user_data.password),
            full_name=user_data.full_name,
            role=Role(user_data.role),
        )
        self.db.add(user)
        await self.db.flush()
        logger.info(f"User registered: {user.username} with role {user.role.value}")
        return user

    async def authenticate(self, username: str, password: str) -> TokenResponse | None:
        """Authenticate user and return tokens."""
        result = await self.db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user or not self.verify_password(password, user.hashed_password):
            logger.warning(f"Failed login attempt for: {username}")
            return None

        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {username}")
            return None

        token_data = {"sub": user.id, "username": user.username, "role": user.role.value}
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)

        logger.info(f"User authenticated: {user.username}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            user=UserResponse.model_validate(user),
        )

    async def get_user_by_id(self, user_id: str) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def list_users(self) -> list[User]:
        result = await self.db.execute(select(User).order_by(User.created_at.desc()))
        return list(result.scalars().all())

    async def seed_default_users(self) -> list[User]:
        """Create default users for development/demo."""
        defaults = [
            UserCreate(
                username="admin",
                email="admin@bankops.ai",
                password="admin123",
                full_name="System Administrator",
                role="ADMIN",
            ),
            UserCreate(
                username="engineer",
                email="engineer@bankops.ai",
                password="engineer123",
                full_name="Support Engineer",
                role="SUPPORT_ENGINEER",
            ),
            UserCreate(
                username="manager",
                email="manager@bankops.ai",
                password="manager123",
                full_name="Incident Manager",
                role="INCIDENT_MANAGER",
            ),
        ]
        users = []
        for user_data in defaults:
            existing = await self.get_user_by_username(user_data.username)
            if not existing:
                user = await self.register_user(user_data)
                users.append(user)
        return users
