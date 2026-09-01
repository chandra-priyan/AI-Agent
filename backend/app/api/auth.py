import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import UserModel
from app.core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)

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
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Registers a new user with unique email and hashed password."""
    email = req.email.strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email address.")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    existing = db.query(UserModel).filter(UserModel.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered.")

    user = UserModel(
        id=f"usr_{uuid.uuid4().hex[:12]}",
        email=email,
        password_hash=hash_password(req.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "email": user.email})
    return {
        "token": token,
        "token_type": "Bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "createdAt": user.created_at.strftime("%Y-%m-%d %H:%M")
        }
    }

@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates user email and password, returning JWT access token."""
    email = req.email.strip().lower()
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token = create_access_token({"sub": user.id, "email": user.email})
    return {
        "token": token,
        "token_type": "Bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "createdAt": user.created_at.strftime("%Y-%m-%d %H:%M")
        }
    }

@router.post("/logout")
def logout():
    """Logs out current user session."""
    return {"message": "Successfully logged out."}

@router.get("/me")
def get_me(current_user: UserModel = Depends(get_current_user)):
    """Retrieves current authenticated user details."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "createdAt": current_user.created_at.strftime("%Y-%m-%d %H:%M")
    }
