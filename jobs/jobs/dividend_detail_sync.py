"""
定时任务脚本：同步所有股票的详细分红历史
"""
import asyncio
import logging
from typing import List, Tuple

import akshare as ak
import pandas as pd

from db.database import async_session_maker
from db.models import AShareStockBasic
from sqlalchemy import select, insert, text

logger = logging.getLogger(__name__)

# 字段范围常量
DIVIDEND_MIN = 0.0
DIVIDEND_MAX = 99999999.9999  
BONUS_SHARE_MIN = 0.0
BONUS_SHARE_MAX = 99999999.9999
TRANSFER_SHARE_MIN = 0
TRANSFER_SHARE_MAX = 2147483647

def _remove_market_prefix(code: str) -> str:
    """移除股票代码的市场前缀"""
    code = str(code).strip()
    prefixes = ['sh', 'sz', 'bj', 'SH', 'SZ', 'BJ']
    for p in prefixes:
        if code.startswith(p):
            return code[len(p):]
    return code

def _format_date(date_val) -> str | None:
    """转换日期格式为 YYYYMMDD"""
    if date_val is None:
        return None
    try:
        if pd.isna(date_val):
            return None
        if hasattr(date_val, 'strftime'):
            return date_val.strftime('%Y%m%d')
        return str(date_val).replace('-', '')[:8]
    except Exception:
        return None

def _clamp_value(value, min_val, max_val, field_name, decimals=4):
    """将值限制在指定范围内，并四舍五入到指定小数位数"""
    if pd.isna(value) or value is None:
        return float(min_val)
    
    try:
        value = float(value)
        if value < min_val:
            logger.debug(f"{field_name} {value} < {min_val}，修正为 {min_val}")
            return float(min_val)
        if value > max_val:
            logger.debug(f"{field_name} {value} > {max_val}，修正为 {max_val}")
            return float(max_val)
        
        rounded = round(value, decimals)
        return float(rounded)
    except (TypeError, ValueError):
        return float(min_val)

async def sync_dividend_detail() -> int:
    """同步所有股票的详细分红历史"""
    async with async_session_maker() as session:
        result = await session.execute(select(AShareStockBasic.code, AShareStockBasic.name))
        stocks = result.all()
        
        logger.info(f"开始同步分红详情数据，共 {len(stocks)} 只股票")
        
        total_processed = 0
        new_records_count = 0
        
        for i, (raw_code, name) in enumerate(stocks):
            code = _remove_market_prefix(raw_code)
            
            if i % 50 == 0:
                logger.info(f"处理进度: {i}/{len(stocks)}")
            
            try:
                df = ak.stock_history_dividend_detail(symbol=code)
                if df is None or df.empty:
                    continue
                
                records = []
                for _, row in df.iterrows():
                    dividend = row.get('派息')
                    if dividend is None or pd.isna(dividend) or dividend <= 0:
                        continue
                    
                    record = {
                        'code': code,
                        'name': name,
                        'announcement_date': _format_date(row.get('公告日期')),
                        'bonus_share': _clamp_value(row.get('送股'), BONUS_SHARE_MIN, BONUS_SHARE_MAX, '送股'),
                        'transfer_share': int(_clamp_value(row.get('转增'), TRANSFER_SHARE_MIN, TRANSFER_SHARE_MAX, '转增')),
                        'dividend': _clamp_value(dividend, DIVIDEND_MIN, DIVIDEND_MAX, '分红'),
                        'progress': row.get('进度'),
                        'ex_dividend_date': _format_date(row.get('除权除息日')),
                        'record_date': _format_date(row.get('股权登记日')),
                        'bonus_share_list_date': _format_date(row.get('红股上市日'))
                    }
                    records.append(record)
                
                if records:
                    insert_stmt = text("""
                        INSERT INTO a_share_dividend_detail 
                        (code, name, announcement_date, bonus_share, transfer_share, 
                         dividend, progress, ex_dividend_date, record_date, bonus_share_list_date)
                        VALUES (:code, :name, :announcement_date, :bonus_share, :transfer_share,
                                :dividend, :progress, :ex_dividend_date, :record_date, :bonus_share_list_date)
                        AS new_data
                        ON DUPLICATE KEY UPDATE 
                            name = new_data.name,
                            bonus_share = new_data.bonus_share,
                            transfer_share = new_data.transfer_share,
                            progress = new_data.progress,
                            ex_dividend_date = new_data.ex_dividend_date,
                            record_date = new_data.record_date,
                            bonus_share_list_date = new_data.bonus_share_list_date,
                            updated_at = CURRENT_TIMESTAMP
                    """)
                    
                    new_count = 0
                    for record in records:
                        result = await session.execute(insert_stmt, record)
                        if result.rowcount == 2:
                            new_count += 1
                    new_records_count += new_count
                    total_processed += len(records)
                    
                    if new_count > 0:
                        logger.info(f"股票 {code}({name}) 新增 {new_count} 条分红记录")
                
            except Exception as e:
                logger.warning(f"同步股票 {code} 分红数据失败: {str(e)[:50]}")
        
        await session.commit()
        logger.info(f"分红详情同步完成，处理记录: {total_processed}，新增记录: {new_records_count}")
        
        return total_processed

async def run_dividend_detail_sync_loop(interval_seconds: int) -> None:
    logger.info(f"Starting dividend detail sync loop, interval: {interval_seconds}s")
    
    while True:
        try:
            logger.info("=== Starting dividend detail sync ===")
            count = await sync_dividend_detail()
            logger.info(f"Dividend detail sync completed, {count} records processed")
        except Exception as e:
            logger.error(f"Dividend detail sync loop error: {str(e)[:200]}")
        
        await asyncio.sleep(interval_seconds)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(sync_dividend_detail())