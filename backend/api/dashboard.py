from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from database import get_db
from models import User
from auth import get_current_active_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    result = await db.execute(select(func.count(User.id)))
    total_users = result.scalar()

    result = await db.execute(select(func.count(User.id)).where(User.is_active == True))
    active_users = result.scalar()

    result = await db.execute(select(func.count(User.id)).where(User.is_superuser == True))
    admin_users = result.scalar()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "admin_users": admin_users,
        "inactive_users": total_users - active_users,
        "system_status": "operational",
        "uptime": "99.9%",
        "last_updated": datetime.now().isoformat()
    }

@router.get("/activity")
async def get_recent_activity(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    recent_users_result = await db.execute(
        select(User).order_by(User.created_at.desc()).limit(10)
    )
    recent_users = recent_users_result.scalars().all()

    activity = []
    for user in recent_users:
        activity.append({
            "type": "user_created",
            "description": f"User '{user.username}' was created",
            "timestamp": user.created_at.isoformat() if user.created_at else None,
            "user": user.username
        })

    return {"activities": activity}
