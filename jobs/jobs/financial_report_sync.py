"""
财务报表同步任务: 从AKShare获取股票季度财务数据
支持获取单季度和多季度数据
支持断点续传
"""

from __future__ import annotations

import asyncio
import logging
import math
import random
from datetime import date
from typing import Any, Optional, List

import pandas as pd
from sqlalchemy import func, select, delete
from sqlalchemy.dialects.mysql import insert as mysql_insert

from db.database import async_session_maker
from db.models import AShareFinancialReport, AShareStockBasic
from utils.sync_progress import (
    create_sync_progress,
    get_sync_progress,
    update_sync_progress,
    complete_sync_progress,
    fail_sync_progress,
)

logger = logging.getLogger(__name__)

TASK_NAME = "financial_report"


def _num(v: Any) -> float | None:
    """Convert value to float, None/NaN returns None"""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except TypeError:
        pass
    try:
        x = float(v)
        if math.isnan(x):
            return None
        return x
    except (TypeError, ValueError):
        return None


def _remove_market_prefix(code: str) -> str:
    """Remove market prefix from stock code (like sh/sz/bj), return pure number"""
    code = str(code).strip()
    if code.lower().startswith('sh') or code.lower().startswith('sz') or code.lower().startswith('bj'):
        return code[2:].zfill(6)
    return code.zfill(6)


def _convert_code(code: str) -> str:
    """Convert pure code to akshare format"""
    code = str(code).strip().zfill(6)
    if code.startswith('6') or code.startswith('9'):
        return f"sh{code}"
    elif code.startswith('8') or code.startswith('4'):
        return f"bj{code}"
    else:
        return f"sz{code}"


def _parse_report_type(period_str: str) -> int:
    """Parse report period string to report type"""
    if not period_str:
        return 4
    month = period_str[-4:-2]
    if month == '03':
        return 1
    elif month == '06':
        return 2
    elif month == '09':
        return 3
    else:
        return 4


def _load_financial_report_sync(code: str, report_type: int = 4) -> Optional[pd.DataFrame]:
    """
    Load financial report data for a single stock
    report_type: 1=一季度, 2=半年报, 3=三季度, 4=年报
    """
    import akshare as ak
    
    try:
        df = ak.stock_financial_abstract_ths(
            symbol=str(code).strip().zfill(6),
            indicator="按报告期"
        )
        if df is not None and not df.empty:
            return df
    except Exception as e:
        logger.warning(f"Failed to load financial report for {code}: {str(e)[:50]}")
    
    return None


def _parse_financial_report(df: pd.DataFrame, code: str) -> List[dict]:
    """Parse DataFrame to financial report records"""
    records = []
    
    for _, row in df.iterrows():
        period = row.get("报告期") or row.get("报表日期")
        if not period:
            continue
        
        period_str = str(period)
        if len(period_str) == 10:
            period_str = period_str.replace('-', '')
        
        record = {
            "code": _remove_market_prefix(code),
            "name": str(row.get("股票简称") or row.get("名称") or "").strip()[:64],
            "report_period": period_str[:8],
            "report_type": _parse_report_type(period_str),
            "eps": _num(row.get("基本每股收益") or row.get("每股收益")),
            "eps_yoy": _num(row.get("每股收益同比增长率") or row.get("基本每股收益同比")),
            "net_profit": _num(row.get("净利润") or row.get("归属于母公司股东的净利润")),
            "net_profit_yoy": _num(row.get("净利润同比增长率") or row.get("归属于母公司股东的净利润同比增长率")),
            "net_profit_deducted": _num(row.get("扣非净利润") or row.get("归属于母公司股东的扣除非经常性损益的净利润")),
            "net_profit_deducted_yoy": _num(row.get("扣非净利润同比增长率")),
            "revenue": _num(row.get("营业收入")),
            "revenue_yoy": _num(row.get("营业收入同比增长率")),
            "roe": _num(row.get("净资产收益率") or row.get("ROE")),
            "roa": _num(row.get("总资产收益率") or row.get("ROA")),
            "gross_margin": _num(row.get("毛利率")),
            "operating_margin": _num(row.get("营业利润率")),
        }
        records.append(record)
    
    return records


async def _save_financial_reports(code: str, records: List[dict]) -> int:
    """保存财务报表数据，先删除再插入"""
    if not records:
        return 0

    async with async_session_maker() as session:
        pure_code = _remove_market_prefix(code)
        
        await session.execute(
            delete(AShareFinancialReport).where(AShareFinancialReport.code == pure_code)
        )
        
        for record in records:
            insert_stmt = mysql_insert(AShareFinancialReport).values(record)
            await session.execute(insert_stmt)
        
        await session.commit()
        logger.info(f"Saved {len(records)} financial report records for {pure_code}")
        return len(records)


async def sync_financial_report_for_stock(code: str) -> int:
    """同步单个股票的财务报表数据"""
    try:
        code = str(code).strip().zfill(6)
        if len(code) != 6:
            logger.debug(f"Skipping invalid stock code: {code}")
            return 0

        logger.info(f"Syncing financial report for {code}")

        df = await asyncio.to_thread(_load_financial_report_sync, code)
        if df is None or df.empty:
            logger.warning(f"No financial report data found for {code}")
            return 0

        records = _parse_financial_report(df, code)
        if not records:
            logger.warning(f"No financial report data found for {code}")
            return 0
        
        records.sort(key=lambda x: x["report_period"])
        return await _save_financial_reports(code, records)
        
    except Exception as e:
        logger.warning(f"Failed to sync financial report for {code}: {str(e)[:100]}")
        return 0


async def sync_financial_report_batch(codes: List[str], start_index: int = 0) -> int:
    """批量同步多个股票的财务报表数据，支持断点续传"""
    total_count = 0
    batch_id = None
    
    if start_index == 0:
        batch_id = await create_sync_progress(TASK_NAME, len(codes))
        logger.info(f"Created sync progress, batch_id: {batch_id}")
    else:
        progress = await get_sync_progress(TASK_NAME)
        if progress:
            _, _, batch_id = progress
        logger.info(f"Resuming from index {start_index}")
    
    try:
        for i in range(start_index, len(codes)):
            code = codes[i]
            logger.info(f"Processing {i+1}/{len(codes)}: {code}")
            count = await sync_financial_report_for_stock(code)
            total_count += count
            
            if batch_id:
                await update_sync_progress(TASK_NAME, batch_id, i + 1)
            
            await asyncio.sleep(random.uniform(0.5, 1.5))
        
        if batch_id:
            await complete_sync_progress(TASK_NAME, batch_id)
        
        return total_count
    
    except Exception as e:
        if batch_id:
            await fail_sync_progress(TASK_NAME, batch_id)
        raise


async def _verify_progress_integrity(codes: List[str], current_index: int) -> bool:
    """验证断点续传的完整性：检查已处理的股票是否有数据"""
    if current_index == 0:
        return True
    
    async with async_session_maker() as session:
        sample_codes = codes[:min(5, current_index)]
        if not sample_codes:
            return True
        
        result = await session.execute(
            select(AShareFinancialReport.code)
            .where(AShareFinancialReport.code.in_(sample_codes))
            .limit(1)
        )
        has_data = result.first() is not None
        
        if not has_data:
            logger.warning(f"Integrity check failed: no financial report data found for previously processed stocks")
            return False
        
        return True


async def sync_financial_report_main(codes: List[str] = None) -> int:
    """主同步函数，支持断点续传"""
    if codes is None:
        codes = []
        
        async with async_session_maker() as session:
            min_market_cap = 400 * 10000 * 10000
            result = await session.execute(
                select(AShareStockBasic.code)
                .where(AShareStockBasic.total_market_cap >= min_market_cap)
            )
            codes = [row[0] for row in result]
        
        if not codes:
            logger.warning("No stocks found in database with market cap >= 400 billion")
            return 0
    
    progress = await get_sync_progress(TASK_NAME)
    start_index = 0
    
    if progress:
        current_index, total_count, batch_id = progress
        if current_index < total_count:
            if await _verify_progress_integrity(codes, current_index):
                logger.info(f"Found interrupted sync, resuming from index {current_index}")
                start_index = current_index
            else:
                logger.warning("Data integrity check failed, resetting to start from beginning")
    
    logger.info(f"Starting financial report sync for {len(codes)} stocks (market cap >= 400.0 billion)")
    return await sync_financial_report_batch(codes, start_index)


async def run_financial_report_sync_loop(interval_seconds: int) -> None:
    """周期性同步财务报表数据"""
    if interval_seconds < 86400:
        logger.warning(f"financial_report_sync_interval_seconds={interval_seconds} too small, set to 86400 (24 hours)")
        interval_seconds = 86400

    sync_count = 0
    while True:
        try:
            sync_count += 1
            logger.info(f"=== Starting Financial Report sync #{sync_count} ===")
            start_time = asyncio.get_event_loop().time()

            result = await sync_financial_report_main()

            elapsed_time = asyncio.get_event_loop().time() - start_time
            logger.info(f"=== Financial Report sync #{sync_count} complete, {result} records in {elapsed_time:.2f}s ===")

            logger.info(f"Next financial report sync in {interval_seconds // 3600} hours")
            await asyncio.sleep(interval_seconds)

        except asyncio.CancelledError:
            logger.info("Financial Report sync task stopped")
            raise
        except Exception as e:
            logger.error(f"Financial Report sync loop error: {str(e)[:100]}")
            await asyncio.sleep(300)