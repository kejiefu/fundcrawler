from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from database import get_db
from models import User
from schemas import UserResponse, UserUpdate
from auth import get_current_active_user, get_password_hash

router = APIRouter(prefix="/api/users", tags=["Users"])

def check_superuser_permission(user: User) -> None:
    """Check if user has admin permissions"""
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

def check_own_resource_permission(current_user: User, resource_id: int) -> None:
    """Check if user has permission to access own resource"""
    if not current_user.is_superuser and current_user.id != resource_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get user object by ID"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

@router.get("/", response_model=List[UserResponse], summary="Get user list")
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[UserResponse]:
    """Get user list (admin only)"""
    check_superuser_permission(current_user)

    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{user_id}", response_model=UserResponse, summary="Get single user")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """Get single user info (admin can access all, regular user can access only self)"""
    check_own_resource_permission(current_user, user_id)

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@router.put("/{user_id}", response_model=UserResponse, summary="Update user info")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """Update user info (admin can update all, regular user can update only self)"""
    check_own_resource_permission(current_user, user_id)

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_data.email is not None:
        user.email = user_data.email
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.is_active is not None and current_user.is_superuser:
        user.is_active = user_data.is_active
    if user_data.password is not None:
        user.hashed_password = get_password_hash(user_data.password)

    await db.commit()
    await db.refresh(user)
    
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete user")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> None:
    """Delete user (admin only, cannot delete self)"""
    check_superuser_permission(current_user)

    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()

@router.get("/stats/count", summary="Get user statistics")
async def get_user_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user statistics (admin only)"""
    check_superuser_permission(current_user)

    result = await db.execute(select(func.count(User.id)))
    total_users = result.scalar()

    result = await db.execute(select(func.count(User.id)).where(User.is_active == True))
    active_users = result.scalar()

    return {"total_users": total_users, "active_users": active_users}
