"""
K线数据同步任务: 从AKShare获取日线数据，计算KDJ和RSI指标
支持多周期同步(日线/周线/月线/年线)
支持断点续传
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

from core.config import settings
from core.kline_sync_core import (
    PERIOD_DAILY, PERIOD_WEEKLY, PERIOD_MONTHLY, PERIOD_YEARLY,
    PERIOD_MAP, THIRTY_DAYS, is_valid_stock_code,
    load_kline_data_from_akshare, parse_kline_data, _convert_code, get_sync_start_date
)
from db.database import async_session_maker
from db.models import AShareKline, AShareIndicator, AShareStockBasic
from utils.sync_progress import (
    create_sync_progress,
    get_sync_progress,
    update_sync_progress,
    complete_sync_progress,
    fail_sync_progress,
)

logger = logging.getLogger(__name__)

TASK_NAME = "kline"


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

    try:
        async with async_session_maker() as session:
            chunk_size = 100
            total_inserted = 0

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
                    result = await session.execute(on_conflict_stmt)
                    total_inserted += result.rowcount

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
                logger.debug(f"Committed chunk {i//chunk_size + 1}, {len(kline_chunk)} records")

            logger.info(f"Saved {total_inserted} kline records (inserted) and {len(kline_records)} indicator records")
            return len(kline_records)
    except Exception as e:
        logger.error(f"Error saving kline data: {str(e)}")
        return 0


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

        try:
            df = await asyncio.wait_for(
                asyncio.to_thread(load_kline_data_from_akshare, ak_code, period, start_date),
                timeout=120
            )
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching kline data for {code}")
            return 0

        if df is None:
            return 0

        kline_records, indicator_records = parse_kline_data(df, ak_code, period)
        if kline_records:
            logger.debug(f"Fetched {len(kline_records)} records for {code}")
        
        return await _save_kline_data(kline_records, indicator_records)

    except Exception as e:
        logger.warning(f"Failed to sync kline for {code}: {str(e)[:100]}")
        return 0


async def sync_kline_batch(codes: List[str], period: int, start_index: int = 0) -> int:
    """批量同步多个股票的K线数据，支持断点续传"""
    total_count = 0
    period_name = PERIOD_MAP[period]
    task_name = f"{TASK_NAME}_{period}"
    batch_id = None
    
    if start_index == 0:
        batch_id = await create_sync_progress(task_name, len(codes))
        logger.info(f"Created sync progress for {period_name}, batch_id: {batch_id}")
    else:
        progress = await get_sync_progress(task_name)
        if progress:
            _, _, batch_id = progress
        logger.info(f"Resuming {period_name} sync from index {start_index}")
    
    try:
        for i in range(start_index, len(codes)):
            code = codes[i]
            logger.info(f"Processing {i+1}/{len(codes)}: {code}")
            count = await sync_kline_for_stock(code, period)
            total_count += count
            
            if batch_id:
                await update_sync_progress(task_name, batch_id, i + 1)
            
            await asyncio.sleep(random.uniform(0.5, 1.5))
        
        if batch_id:
            await complete_sync_progress(task_name, batch_id)
        
        return total_count
    
    except Exception as e:
        if batch_id:
            await fail_sync_progress(task_name, batch_id)
        raise


async def _verify_kline_progress_integrity(codes: List[str], period: int, current_index: int) -> bool:
    """验证K线同步断点续传的完整性：检查已处理的股票是否有数据"""
    if current_index == 0:
        return True
    
    async with async_session_maker() as session:
        if current_index > len(codes):
            return False
        
        sample_code = codes[current_index - 1]
        result = await session.execute(
            select(AShareKline.code)
            .where(AShareKline.code == sample_code)
            .where(AShareKline.period == period)
            .limit(1)
        )
        has_data = result.first() is not None
        
        if not has_data:
            logger.warning(f"Integrity check failed for {PERIOD_MAP[period]}: no data found for {sample_code}")
            return False
        
        return True


async def sync_kline_all_periods(codes: List[str]) -> Dict[int, int]:
    """同步所有周期的K线数据，支持断点续传"""
    results = {}
    for period in [PERIOD_DAILY, PERIOD_WEEKLY, PERIOD_MONTHLY, PERIOD_YEARLY]:
        period_name = PERIOD_MAP[period]
        task_name = f"{TASK_NAME}_{period}"
        
        progress = await get_sync_progress(task_name)
        start_index = 0
        
        if progress:
            current_index, total_count, _ = progress
            if current_index < total_count:
                if await _verify_kline_progress_integrity(codes, period, current_index):
                    logger.info(f"Found interrupted {period_name} sync, resuming from index {current_index}")
                    start_index = current_index
                else:
                    logger.warning(f"Data integrity check failed for {period_name}, resetting to start from beginning")
        
        logger.info(f"=== Syncing {period_name} data ===")
        count = await sync_kline_batch(codes, period, start_index)
        results[period] = count
        logger.info(f"=== {period_name} sync complete, {count} records ===")

    return results


async def sync_kline_main(codes: List[str] = None) -> Dict[int, int]:
    """主同步函数"""
    if codes is None:
        codes = []

        async with async_session_maker() as session:
            min_market_cap = settings.kline_sync_min_market_cap_billion * 10**8
            result = await session.execute(
                select(AShareStockBasic.code)
                .where(AShareStockBasic.total_market_cap >= min_market_cap)
            )
            codes = [row[0] for row in result]

        if not codes:
            logger.warning(f"No stocks found in database with market cap >= {settings.kline_sync_min_market_cap_billion} billion")
            return {}

    logger.info(f"Starting kline sync for {len(codes)} stocks (market cap >= {settings.kline_sync_min_market_cap_billion} billion)")
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
