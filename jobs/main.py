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
from jobs.kline_sync import run_kline_sync_loop
from jobs.financial_report_sync import run_financial_report_sync_loop

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

    tasks: list[asyncio.Task[None]] = []
    startup_delay = 3
    
    if settings.a_share_basic_sync_enabled:
        task = asyncio.create_task(
            run_a_share_stock_basic_sync_loop(
                settings.a_share_basic_sync_interval_seconds
            )
        )
        tasks.append(task)
        logger.info(f"A-share basic info sync task started, interval: {settings.a_share_basic_sync_interval_seconds}s")
        await asyncio.sleep(startup_delay)

    if settings.kline_sync_enabled:
        task = asyncio.create_task(
            run_kline_sync_loop(
                settings.kline_sync_interval_seconds
            )
        )
        tasks.append(task)
        logger.info(f"Kline sync task started, interval: {settings.kline_sync_interval_seconds}s")
        await asyncio.sleep(startup_delay)

    if settings.financial_report_sync_enabled:
        task = asyncio.create_task(
            run_financial_report_sync_loop(
                settings.financial_report_sync_interval_seconds
            )
        )
        tasks.append(task)
        logger.info(f"Financial report sync task started, interval: {settings.financial_report_sync_interval_seconds}s")

    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        logger.info("Jobs service stopped")


async def main():
    """Main entry point"""
    logger.info("=" * 50)
    logger.info("Jobs service starting...")
    logger.info(f"A-share basic sync enabled: {settings.a_share_basic_sync_enabled}")
    logger.info(f"Kline sync enabled: {settings.kline_sync_enabled}")
    logger.info(f"Financial report sync enabled: {settings.financial_report_sync_enabled}")
    logger.info("=" * 50)

    async with lifespan():
        while True:
            await asyncio.sleep(3600)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted signal received, exiting...")
