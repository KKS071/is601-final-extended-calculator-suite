# File: app/auth/jwt.py
# Purpose: Password hashing and JWT token creation/decoding utilities.
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
from uuid import UUID

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.schemas.token import TokenType

settings = get_settings()

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_token(
    user_id: Union[str, UUID],
    token_type: TokenType,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT for the given user ID and token type."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    elif token_type == TokenType.ACCESS:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    if isinstance(user_id, UUID):
        user_id = str(user_id)

    payload = {
        "sub":  user_id,
        "type": token_type.value,
        "exp":  expire,
        "iat":  datetime.now(timezone.utc),
        "jti":  secrets.token_hex(16),
    }

    secret = (
        settings.JWT_SECRET_KEY if token_type == TokenType.ACCESS else settings.JWT_REFRESH_SECRET_KEY
    )

    try:
        return jwt.encode(payload, secret, algorithm=settings.ALGORITHM)
    except Exception as e:  # pragma: no cover
        raise HTTPException(  # pragma: no cover
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create token: {str(e)}",
        )


def decode_token(token: str, token_type: TokenType) -> dict[str, Any]:
    """Decode and verify a JWT. Raises HTTPException on failure."""
    secret = (
        settings.JWT_SECRET_KEY if token_type == TokenType.ACCESS else settings.JWT_REFRESH_SECRET_KEY
    )
    try:
        payload = jwt.decode(token, secret, algorithms=[settings.ALGORITHM])
        if payload.get("type") != token_type.value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
