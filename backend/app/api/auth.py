import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)
from app.repositories.mongo_repository import MongoRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    token_type: str = "Bearer"
    user: dict


@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest):
    """Registers a new user in MongoDB Atlas with unique email and hashed password."""
    email = req.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email address.")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    existing = MongoRepository.get_user_by_email(email)
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered.")

    uid = f"usr_{uuid.uuid4().hex[:12]}"
    pwd_hash = hash_password(req.password)
    user_doc = MongoRepository.create_user(email=email, password_hash=pwd_hash, user_id=uid)

    token = create_access_token({"sub": uid, "email": email})
    created_at_val = user_doc.get("created_at", "Just now")[:16].replace("T", " ")
    
    return {
        "token": token,
        "token_type": "Bearer",
        "user": {
            "id": uid,
            "email": email,
            "createdAt": created_at_val
        }
    }


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest):
    """Authenticates user email and password against MongoDB Atlas, returning JWT access token."""
    email = req.email.strip().lower()
    user = MongoRepository.get_user_by_email(email)
    if not user or not verify_password(req.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    uid = str(user.get("_id", user.get("id")))
    token = create_access_token({"sub": uid, "email": email})
    created_at_val = user.get("created_at", "Just now")[:16].replace("T", " ")

    return {
        "token": token,
        "token_type": "Bearer",
        "user": {
            "id": uid,
            "email": email,
            "createdAt": created_at_val
        }
    }


@router.post("/logout")
def logout():
    """Logs out current user session."""
    return {"message": "Successfully logged out."}


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """Retrieves current authenticated user details from MongoDB Atlas."""
    uid = str(current_user.get("_id", current_user.get("id")))
    created_at_val = current_user.get("created_at", "Just now")[:16].replace("T", " ")
    return {
        "id": uid,
        "email": current_user.get("email"),
        "createdAt": created_at_val
    }
