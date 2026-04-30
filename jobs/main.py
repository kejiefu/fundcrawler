"""
Jobs 服务独立启动入口
支持 A 股基本信息定时同步任务，可扩展更多定时任务
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from core.config import settings
from db.database import init_db
from jobs.a_share_basic_sync import run_a_share_stock_basic_sync_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan():
    """生命周期管理：启动时初始化，关闭时清理"""
    await init_db()
    logger.info("Jobs 服务数据库初始化完成")

    sync_task: asyncio.Task[None] | None = None
    if settings.a_share_basic_sync_enabled:
        sync_task = asyncio.create_task(
            run_a_share_stock_basic_sync_loop(
                settings.a_share_basic_sync_interval_seconds
            )
        )
        logger.info(f"A 股基本信息同步任务已启动，间隔 {settings.a_share_basic_sync_interval_seconds} 秒")

    try:
        yield
    finally:
        if sync_task is not None:
            sync_task.cancel()
            try:
                await sync_task
            except asyncio.CancelledError:
                logger.info("A 股基本信息同步任务已停止")
        logger.info("Jobs 服务已关闭")


async def main():
    """主入口"""
    logger.info("=" * 50)
    logger.info("Jobs 服务启动中...")
    logger.info(f"A 股同步启用: {settings.a_share_basic_sync_enabled}")
    logger.info(f"同步间隔: {settings.a_share_basic_sync_interval_seconds} 秒")
    logger.info("=" * 50)

    async with lifespan():
        while True:
            await asyncio.sleep(3600)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("收到中断信号，退出...")
