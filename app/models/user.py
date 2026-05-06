# File: app/models/user.py
# Purpose: User SQLAlchemy model. Uses GUID type for SQLite+Postgres compat.
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import Boolean, Column, DateTime, String, or_
from sqlalchemy.orm import relationship

from app.core.config import get_settings
from app.database import Base
from app.models.calculation import GUID, Calculation  # noqa: F401

settings = get_settings()


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id          = Column(GUID(), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    username    = Column(String(50), unique=True, nullable=False, index=True)
    email       = Column(String, unique=True, nullable=False, index=True)
    password    = Column(String, nullable=False)
    first_name  = Column(String(50), nullable=False)
    last_name   = Column(String(50), nullable=False)
    is_active   = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at  = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at  = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    last_login  = Column(DateTime(timezone=True), nullable=True)

    calculations = relationship("Calculation", back_populates="user", cascade="all, delete-orphan")

    def __init__(self, *args, **kwargs):
        if "hashed_password" in kwargs:
            kwargs["password"] = kwargs.pop("hashed_password")
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f"<User(name={self.first_name} {self.last_name}, email={self.email})>"

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.updated_at = utcnow()
        return self

    @property
    def hashed_password(self):
        return self.password

    def verify_password(self, plain_password: str) -> bool:
        from app.auth.jwt import verify_password
        return verify_password(plain_password, self.password)

    @classmethod
    def hash_password(cls, password: str) -> str:
        from app.auth.jwt import get_password_hash
        return get_password_hash(password)

    @classmethod
    def register(cls, db, user_data: dict):
        password = user_data.get("password")
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        existing = db.query(cls).filter(
            or_(cls.email == user_data["email"], cls.username == user_data["username"])
        ).first()
        if existing:
            raise ValueError("Username or email already exists")
        user = cls(
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            email=user_data["email"],
            username=user_data["username"],
            password=cls.hash_password(password),
            is_active=True,
            is_verified=False,
        )
        db.add(user)
        return user

    @classmethod
    def authenticate(cls, db, username_or_email: str, password: str):
        user = db.query(cls).filter(
            or_(cls.username == username_or_email, cls.email == username_or_email)
        ).first()
        if not user or not user.verify_password(password):
            return None
        user.last_login = utcnow()
        db.flush()
        access_token  = cls.create_access_token({"sub": str(user.id)})
        refresh_token = cls.create_refresh_token({"sub": str(user.id)})
        expires_at    = utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return {
            "access_token":  access_token,
            "refresh_token": refresh_token,
            "token_type":    "bearer",
            "expires_at":    expires_at,
            "user":          user,
        }

    @classmethod
    def create_access_token(cls, data: dict) -> str:
        from app.auth.jwt import create_token
        from app.schemas.token import TokenType
        return create_token(data["sub"], TokenType.ACCESS)

    @classmethod
    def create_refresh_token(cls, data: dict) -> str:
        from app.auth.jwt import create_token
        from app.schemas.token import TokenType
        return create_token(data["sub"], TokenType.REFRESH)

    @classmethod
    def verify_token(cls, token):
        from app.core.config import settings as cfg
        if not token:
            return None
        from jose import jwt, JWTError
        try:
            payload = jwt.decode(token, cfg.JWT_SECRET_KEY, algorithms=[cfg.ALGORITHM])
            sub = payload.get("sub")
            if sub is None:
                return None
            return uuid.UUID(sub)
        except (JWTError, ValueError, TypeError):
            return None
