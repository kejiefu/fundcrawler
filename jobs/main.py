"""
Jobs service independent entry point
Supports A-share basic info sync task, can be extended with more scheduled tasks
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
    """Lifecycle management: initialize on startup, cleanup on shutdown"""
    await init_db()
    logger.info("Jobs service database initialization complete")

    sync_task: asyncio.Task[None] | None = None
    if settings.a_share_basic_sync_enabled:
        sync_task = asyncio.create_task(
            run_a_share_stock_basic_sync_loop(
                settings.a_share_basic_sync_interval_seconds
            )
        )
        logger.info(f"A-share basic info sync task started, interval: {settings.a_share_basic_sync_interval_seconds}s")

    try:
        yield
    finally:
        if sync_task is not None:
            sync_task.cancel()
            try:
                await sync_task
            except asyncio.CancelledError:
                logger.info("A-share basic info sync task stopped")
        logger.info("Jobs service stopped")


async def main():
    """Main entry point"""
    logger.info("=" * 50)
    logger.info("Jobs service starting...")
    logger.info(f"A-share sync enabled: {settings.a_share_basic_sync_enabled}")
    logger.info(f"Sync interval: {settings.a_share_basic_sync_interval_seconds}s")
    logger.info("=" * 50)

    async with lifespan():
        while True:
            await asyncio.sleep(3600)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted signal received, exiting...")
