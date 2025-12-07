"""
FastAPI router for user registration, login, email verification, avatar update, and /me endpoint with rate limiting.
"""
import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import cloudinary
import cloudinary.uploader
from app.database import SessionLocal
from app.schemas.user import UserCreate, UserOut, Token
from app.crud.user import create_user, authenticate_user, verify_user_email, update_avatar
from app.utils.auth import create_access_token, decode_access_token, send_verification_email
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def get_db():
    """Dependency to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user and send verification email."""
    db_user = create_user(db, user)
    send_verification_email(db_user.email, db_user.id)
    return db_user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token({"user_id": user.id, "email": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/verify/{user_id}", response_model=UserOut)
async def verify_email(user_id: int, db: Session = Depends(get_db)):
    """Verify user email by user ID."""
    user = verify_user_email(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/avatar", response_model=UserOut)
async def update_user_avatar(token: str = Depends(oauth2_scheme), file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Update user avatar using Cloudinary."""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("user_id")
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET")
    )
    result = cloudinary.uploader.upload(file.file)
    avatar_url = result.get("secure_url")
    user = update_avatar(db, user_id, avatar_url)
    return user

@router.get("/me", response_model=UserOut)
@limiter.limit("5/minute")
async def get_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get current user info (rate limited)."""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
