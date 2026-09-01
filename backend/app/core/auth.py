import os
import time
import base64
import json
import hmac
import hashlib
import secrets
import logging
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.database import SessionLocal, get_db
from app.db.models import UserModel

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "autonomous_data_scientist_super_secret_jwt_key_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 60 * 60 * 24 * 7  # 7 days

security_scheme = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """Hashes password using PBKDF2 HMAC SHA256 with a unique random salt."""
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return base64.b64encode(salt + key).decode('ascii')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against stored PBKDF2 hash."""
    try:
        data = base64.b64decode(hashed_password.encode('ascii'))
        salt = data[:16]
        stored_key = data[16:]
        computed_key = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
        return hmac.compare_digest(stored_key, computed_key)
    except Exception:
        return False

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')

def _b64url_decode(encoded_str: str) -> bytes:
    padding = '=' * (4 - (len(encoded_str) % 4))
    return base64.urlsafe_b64encode(base64.urlsafe_b64decode(encoded_str + padding))

def create_access_token(data: Dict[str, Any], expires_delta_seconds: Optional[int] = None) -> str:
    """Creates signed HS256 JWT access token."""
    header = {"alg": "HS256", "typ": "JWT"}
    header_json = json.dumps(header, separators=(',', ':')).encode('utf-8')
    header_b64 = _b64url_encode(header_json)

    payload = data.copy()
    expire = int(time.time()) + (expires_delta_seconds or ACCESS_TOKEN_EXPIRE_SECONDS)
    payload["exp"] = expire
    payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    payload_b64 = _b64url_encode(payload_json)

    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates signed JWT token."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts

        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
        actual_sig = base64.urlsafe_b64decode(sig_b64 + '=' * (4 - (len(sig_b64) % 4)))

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload_json = base64.urlsafe_b64decode(payload_b64 + '=' * (4 - (len(payload_b64) % 4))).decode('utf-8')
        payload = json.loads(payload_json)

        if payload.get("exp") and time.time() > payload["exp"]:
            return None

        return payload
    except Exception as e:
        logger.warning(f"Failed to decode token: {e}")
        return None

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> UserModel:
    """FastAPI security dependency enforcing valid user authentication."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    db.expire_all()
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Optional[UserModel]:
    """FastAPI security dependency returning user if valid token provided, else None."""
    if not credentials or not credentials.credentials:
        return None
    try:
        return get_current_user(credentials, db)
    except Exception:
        return None
