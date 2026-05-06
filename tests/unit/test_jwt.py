# File: tests/unit/test_jwt.py
# Purpose: Unit tests for JWT creation, decoding, and password hashing utilities.
import time
import uuid
from datetime import timedelta

import pytest
from fastapi import HTTPException

from app.auth.jwt import (
    create_token, decode_token,
    get_password_hash, verify_password,
)
from app.schemas.token import TokenType


def test_hash_and_verify():
    hashed = get_password_hash("SecurePass123!")
    assert verify_password("SecurePass123!", hashed)

def test_wrong_password_fails():
    hashed = get_password_hash("Correct123!")
    assert not verify_password("Wrong123!", hashed)

def test_create_access_token():
    user_id = str(uuid.uuid4())
    token   = create_token(user_id, TokenType.ACCESS)
    assert isinstance(token, str)

def test_create_refresh_token():
    user_id = str(uuid.uuid4())
    token   = create_token(user_id, TokenType.REFRESH)
    assert isinstance(token, str)

def test_decode_valid_access_token():
    user_id = str(uuid.uuid4())
    token   = create_token(user_id, TokenType.ACCESS)
    payload = decode_token(token, TokenType.ACCESS)
    assert payload["sub"] == user_id

def test_decode_valid_refresh_token():
    user_id = str(uuid.uuid4())
    token   = create_token(user_id, TokenType.REFRESH)
    payload = decode_token(token, TokenType.REFRESH)
    assert payload["sub"] == user_id

def test_wrong_token_type_raises():
    user_id = str(uuid.uuid4())
    token   = create_token(user_id, TokenType.ACCESS)
    with pytest.raises(HTTPException) as exc:
        decode_token(token, TokenType.REFRESH)
    assert exc.value.status_code == 401

def test_expired_token_raises():
    user_id = str(uuid.uuid4())
    token   = create_token(user_id, TokenType.ACCESS, expires_delta=timedelta(seconds=-1))
    with pytest.raises(HTTPException) as exc:
        decode_token(token, TokenType.ACCESS)
    assert exc.value.status_code == 401

def test_invalid_token_raises():
    with pytest.raises(HTTPException) as exc:
        decode_token("not.a.valid.token", TokenType.ACCESS)
    assert exc.value.status_code == 401

def test_uuid_user_id_accepted():
    user_id = uuid.uuid4()
    token   = create_token(user_id, TokenType.ACCESS)
    payload = decode_token(token, TokenType.ACCESS)
    assert payload["sub"] == str(user_id)

def test_custom_expiry():
    user_id = str(uuid.uuid4())
    token   = create_token(user_id, TokenType.ACCESS, expires_delta=timedelta(hours=2))
    payload = decode_token(token, TokenType.ACCESS)
    assert payload["sub"] == user_id

def test_jti_present():
    user_id = str(uuid.uuid4())
    token   = create_token(user_id, TokenType.ACCESS)
    payload = decode_token(token, TokenType.ACCESS)
    assert "jti" in payload

def test_unique_jti_per_token():
    uid   = str(uuid.uuid4())
    tok1  = create_token(uid, TokenType.ACCESS)
    tok2  = create_token(uid, TokenType.ACCESS)
    p1    = decode_token(tok1, TokenType.ACCESS)
    p2    = decode_token(tok2, TokenType.ACCESS)
    assert p1["jti"] != p2["jti"]
