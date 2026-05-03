"""
K线数据同步任务: 从AKShare获取日线数据，计算KDJ和RSI指标
支持多周期同步(日线/周线/月线/年线)
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Dict, Optional, List
from sqlalchemy import func, select
from sqlalchemy.dialects.mysql import insert as mysql_insert

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.kline_sync_core import (
    PERIOD_DAILY, PERIOD_WEEKLY, PERIOD_MONTHLY, PERIOD_YEARLY,
    PERIOD_MAP, THIRTY_DAYS, is_valid_stock_code,
    load_kline_data_from_akshare, parse_kline_data, _convert_code, get_sync_start_date
)
from db.database import async_session_maker
from db.models import AShareKline, AShareIndicator

logger = logging.getLogger(__name__)


async def get_earliest_trade_date(code: str, period: int) -> Optional[str]:
    """获取指定股票和周期最早的交易日期"""
    async with async_session_maker() as session:
        result = await session.execute(
            select(func.min(AShareKline.trade_date))
            .where(AShareKline.code == code[-6:])
            .where(AShareKline.period == period)
        )
        earliest_date = result.scalar_one_or_none()
        return earliest_date


async def needs_full_sync(code: str, period: int) -> bool:
    """检查是否需要全量同步（数据库中没有该股票该周期的数据）"""
    earliest_date = await get_earliest_trade_date(code, period)
    return earliest_date is None


async def _save_kline_data(kline_records: list, indicator_records: list) -> int:
    """保存K线数据和指标数据"""
    if not kline_records:
        return 0

    async with async_session_maker() as session:
        chunk_size = 100

        for i in range(0, len(kline_records), chunk_size):
            kline_chunk = kline_records[i:i + chunk_size]
            indicator_chunk = indicator_records[i:i + chunk_size]

            for kline in kline_chunk:
                insert_stmt = mysql_insert(AShareKline).values(kline)
                on_conflict_stmt = insert_stmt.on_duplicate_key_update(
                    open_price=insert_stmt.inserted.open_price,
                    close_price=insert_stmt.inserted.close_price,
                    high_price=insert_stmt.inserted.high_price,
                    low_price=insert_stmt.inserted.low_price,
                    volume=insert_stmt.inserted.volume,
                    amount=insert_stmt.inserted.amount,
                    prev_close=insert_stmt.inserted.prev_close,
                    change_pct=insert_stmt.inserted.change_pct,
                    change_amount=insert_stmt.inserted.change_amount,
                    amplitude=insert_stmt.inserted.amplitude,
                    updated_at=func.now()
                )
                await session.execute(on_conflict_stmt)

            for indicator in indicator_chunk:
                insert_stmt = mysql_insert(AShareIndicator).values(indicator)
                on_conflict_stmt = insert_stmt.on_duplicate_key_update(
                    k_value=insert_stmt.inserted.k_value,
                    d_value=insert_stmt.inserted.d_value,
                    j_value=insert_stmt.inserted.j_value,
                    rsi_6=insert_stmt.inserted.rsi_6,
                    rsi_12=insert_stmt.inserted.rsi_12,
                    rsi_24=insert_stmt.inserted.rsi_24,
                    updated_at=func.now()
                )
                await session.execute(on_conflict_stmt)

            await session.commit()

        logger.info(f"Saved {len(kline_records)} kline records and {len(indicator_records)} indicator records")
        return len(kline_records)


async def sync_kline_for_stock(code: str, period: int) -> int:
    """同步单个股票的K线数据"""
    try:
        if not is_valid_stock_code(code):
            logger.debug(f"Skipping invalid stock code: {code}")
            return 0

        needs_full = await needs_full_sync(code, period)

        if needs_full:
            logger.info(f"首次同步，获取{code}上市以来的全部{PERIOD_MAP[period]}数据")
        else:
            logger.info(f"增量同步{code}的{PERIOD_MAP[period]}数据")

        ak_code = _convert_code(code)
        start_date = get_sync_start_date(needs_full, period)

        df = await asyncio.to_thread(load_kline_data_from_akshare, ak_code, period, start_date)
        if df is None:
            return 0

        kline_records, indicator_records = parse_kline_data(df, ak_code, period)
        return await _save_kline_data(kline_records, indicator_records)

    except Exception as e:
        logger.warning(f"Failed to sync kline for {code}: {str(e)[:100]}")
        return 0


async def sync_kline_batch(codes: List[str], period: int) -> int:
    """批量同步多个股票的K线数据"""
    total_count = 0
    for i, code in enumerate(codes):
        logger.info(f"Processing {i+1}/{len(codes)}: {code}")
        count = await sync_kline_for_stock(code, period)
        total_count += count

        await asyncio.sleep(random.uniform(0.5, 1.5))

    return total_count


async def sync_kline_all_periods(codes: List[str]) -> Dict[int, int]:
    """同步所有周期的K线数据"""
    results = {}
    for period in [PERIOD_DAILY, PERIOD_WEEKLY, PERIOD_MONTHLY, PERIOD_YEARLY]:
        logger.info(f"=== Syncing {PERIOD_MAP[period]} data ===")
        count = await sync_kline_batch(codes, period)
        results[period] = count
        logger.info(f"=== {PERIOD_MAP[period]} sync complete, {count} records ===")

    return results


async def sync_kline_main(codes: List[str] = None) -> Dict[int, int]:
    """主同步函数"""
    if codes is None:
        codes = []

        async with async_session_maker() as session:
            from db.models import AShareStockBasic
            from sqlalchemy import select
            result = await session.execute(select(AShareStockBasic.code))
            codes = [row[0] for row in result]

        if not codes:
            logger.warning("No stocks found in database")
            return {}

    logger.info(f"Starting kline sync for {len(codes)} stocks")
    return await sync_kline_all_periods(codes)


async def run_kline_sync_loop(interval_seconds: int) -> None:
    """周期性同步K线数据"""
    if interval_seconds < 3600:
        logger.warning(f"kline_sync_interval_seconds={interval_seconds} too small, set to 3600")
        interval_seconds = 3600

    sync_count = 0
    while True:
        try:
            sync_count += 1
            logger.info(f"=== Starting Kline sync #{sync_count} ===")
            start_time = asyncio.get_event_loop().time()

            results = await sync_kline_main()

            elapsed_time = asyncio.get_event_loop().time() - start_time
            total_records = sum(results.values())
            logger.info(f"=== Kline sync #{sync_count} complete, {total_records} records in {elapsed_time:.2f}s ===")

            logger.info(f"Next kline sync in {interval_seconds // 60} minutes")
            await asyncio.sleep(interval_seconds)

        except asyncio.CancelledError:
            logger.info("Kline sync task stopped")
            raise
        except Exception as e:
            logger.error(f"Kline sync loop error: {str(e)[:100]}")
            await asyncio.sleep(60)
