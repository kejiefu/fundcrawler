from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import User
from schemas import LoginRequest, Token, UserResponse, UserCreate
from auth import authenticate_user, create_access_token, get_password_hash, get_current_user
from core.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login", response_model=Token, summary="User login")
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)) -> Token:
    """User login interface, verify username and password and return JWT Token"""
    user = await authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="User registration")
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)) -> UserResponse:
    """User registration interface, create new user account"""
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already registered")

    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user

@router.get("/me", response_model=UserResponse, summary="Get current user info")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Get detailed information of the currently logged in user"""
    return current_user
