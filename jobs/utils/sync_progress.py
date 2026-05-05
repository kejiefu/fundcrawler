import logging
import uuid
from typing import Optional, Tuple
from sqlalchemy import select, update, delete, text
from sqlalchemy.dialects.mysql import insert as mysql_insert

from db.database import async_session_maker
from db.models import SyncProgress

logger = logging.getLogger(__name__)


async def create_sync_progress(task_name: str, total_count: int) -> str:
    """创建同步进度记录，返回批次ID"""
    batch_id = str(uuid.uuid4())
    
    async with async_session_maker() as session:
        try:
            await session.execute(
                delete(SyncProgress).where(SyncProgress.task_name == task_name)
            )
            
            await session.execute(
                mysql_insert(SyncProgress).values(
                    task_name=task_name,
                    batch_id=batch_id,
                    current_index=0,
                    total_count=total_count,
                    status="running"
                )
            )
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.warning(f"Failed to create sync progress: {e}")
    
    return batch_id


async def get_sync_progress(task_name: str) -> Optional[Tuple[int, int, str]]:
    """获取同步进度：(current_index, total_count, batch_id)"""
    async with async_session_maker() as session:
        try:
            result = await session.execute(
                select(SyncProgress.current_index, SyncProgress.total_count, SyncProgress.batch_id)
                .where(SyncProgress.task_name == task_name)
                .where(SyncProgress.status == "running")
            )
            row = result.first()
            if row:
                return row[0], row[1], row[2]
        except Exception as e:
            logger.warning(f"Failed to get sync progress: {e}")
        return None


async def update_sync_progress(task_name: str, batch_id: str, current_index: int) -> None:
    """更新同步进度，使用独立事务避免死锁"""
    async with async_session_maker() as session:
        try:
            await session.execute(
                update(SyncProgress)
                .where(SyncProgress.task_name == task_name)
                .where(SyncProgress.batch_id == batch_id)
                .values(current_index=current_index)
            )
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.warning(f"Failed to update sync progress: {e}")


async def complete_sync_progress(task_name: str, batch_id: str) -> None:
    """标记同步完成"""
    async with async_session_maker() as session:
        try:
            await session.execute(
                update(SyncProgress)
                .where(SyncProgress.task_name == task_name)
                .where(SyncProgress.batch_id == batch_id)
                .values(status="completed", current_index=0)
            )
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.warning(f"Failed to complete sync progress: {e}")


async def fail_sync_progress(task_name: str, batch_id: str) -> None:
    """标记同步失败"""
    async with async_session_maker() as session:
        try:
            await session.execute(
                update(SyncProgress)
                .where(SyncProgress.task_name == task_name)
                .where(SyncProgress.batch_id == batch_id)
                .values(status="failed")
            )
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.warning(f"Failed to mark sync progress as failed: {e}")
