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
    """检查用户是否具有管理员权限"""
    if not user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")

def check_own_resource_permission(current_user: User, resource_id: int) -> None:
    """检查用户是否有权访问自己的资源（非管理员只能访问自己的数据）"""
    if not current_user.is_superuser and current_user.id != resource_id:
        raise HTTPException(status_code=403, detail="权限不足")

async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """根据ID获取用户对象"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

@router.get("/", response_model=List[UserResponse], summary="获取用户列表")
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[UserResponse]:
    """获取用户列表（仅限管理员）"""
    check_superuser_permission(current_user)

    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{user_id}", response_model=UserResponse, summary="获取单个用户")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """获取单个用户信息（管理员可访问所有用户，普通用户只能访问自己）"""
    check_own_resource_permission(current_user, user_id)

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return user

@router.put("/{user_id}", response_model=UserResponse, summary="更新用户信息")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """更新用户信息（管理员可更新所有用户，普通用户只能更新自己）"""
    check_own_resource_permission(current_user, user_id)

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 更新字段
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

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除用户")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> None:
    """删除用户（仅限管理员，且不能删除自己）"""
    check_superuser_permission(current_user)

    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="无法删除自己")

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    await db.delete(user)
    await db.commit()

@router.get("/stats/count", summary="获取用户统计")
async def get_user_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户统计数据（仅限管理员）"""
    check_superuser_permission(current_user)

    result = await db.execute(select(func.count(User.id)))
    total_users = result.scalar()

    result = await db.execute(select(func.count(User.id)).where(User.is_active == True))
    active_users = result.scalar()

    return {"total_users": total_users, "active_users": active_users}
