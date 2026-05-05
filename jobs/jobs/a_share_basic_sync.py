"""
A-share basic info sync: pull full market via AKShare Sina interface, 
write to a_share_stock_basic table
Blocking IO (pandas) runs in asyncio.to_thread to avoid blocking event loop
"""

from __future__ import annotations

import asyncio
import logging
import math
import random
from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy import func
from sqlalchemy.dialects.mysql import insert as mysql_insert

from db.database import async_session_maker
from db.models import AShareStockBasic

logger = logging.getLogger(__name__)


def _infer_board_label(code: str) -> str:
    """Infer exchange/board from security code"""
    c = str(code).strip().zfill(6)
    if len(c) < 6:
        return "Other"
    p2, p3 = c[:2], c[:3]
    if p2 in ("83", "87", "88", "92") or p3 == "430" or (p3 == "920"):
        return "BSE"
    if p3 in ("688", "689"):
        return "STAR Market"
    if p2 == "60":
        return "SH Main Board"
    if p3 in ("000", "001", "002", "003"):
        return "SZ Main Board"
    if p3 in ("300", "301"):
        return "ChiNext"
    return "Other"


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
        if math.isnan(x) or math.isinf(x):
            return None
        return x
    except (TypeError, ValueError):
        return None


def _validate_dividend_yield(value: float | None) -> float | None:
    """Validate dividend yield value before database insertion"""
    if value is None:
        return None
    
    try:
        value = float(value)
        if math.isnan(value) or math.isinf(value):
            return None
        
        max_value = 99999999.9999
        min_value = -99999999.9999
        
        if value > max_value or value < min_value:
            logger.debug(f"Dividend yield {value} out of range, setting to None")
            return None
        
        return round(value, 4)
    except (TypeError, ValueError):
        return None


def _load_spot_dataframe_sync() -> pd.DataFrame:
    """
    Sync load A-share realtime market data
    Priority: East Money interface (more fields like PE/PB), fallback to Sina
    """
    import akshare as ak
    
    try:
        df = ak.stock_zh_a_spot_em()
        if df is not None and not df.empty:
            logger.info("Using East Money interface for A-share data")
            return df
    except Exception as e:
        logger.warning(f"East Money interface failed, fallback to Sina: {str(e)[:50]}")
    
    logger.info("Using Sina interface for A-share data")
    return ak.stock_zh_a_spot()


def _get_single_stock_data_sync(code: str) -> dict | None:
    """
    Get realtime data for a single stock
    :param code: Pure stock code (6 digits)
    :return: Dictionary with stock data or None
    """
    import akshare as ak
    
    code = str(code).strip().zfill(6)
    
    try:
        if code.startswith('6'):
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                df['代码'] = df['代码'].astype(str).str.zfill(6)
                row = df[df['代码'] == code]
                if not row.empty:
                    return row.iloc[0].to_dict()
        else:
            df = ak.stock_zh_a_spot()
            if df is not None and not df.empty:
                df['代码'] = df['代码'].astype(str).str.zfill(6)
                row = df[df['代码'] == code]
                if not row.empty:
                    return row.iloc[0].to_dict()
    except Exception as e:
        logger.warning(f"Failed to get single stock data for {code}: {str(e)[:50]}")
    
    return None


def _get_single_stock_dividend_sync(code: str) -> tuple[float | None, str | None]:
    """
    Get dividend yield for a single stock using Sina's dividend history
    :param code: Pure stock code (6 digits)
    :return: (dividend_yield, dividend_date)
    """
    return _calculate_recent_year_dividend(code), None


def _get_single_stock_pe_pb_sync(code: str) -> tuple[float | None, float | None]:
    """
    Get PE and PB for a single stock from Tencent API
    :param code: Pure stock code (6 digits)
    :return: (pe_dynamic, pb)
    """
    import requests
    
    code = str(code).strip().zfill(6)
    
    if code.startswith('6'):
        tencent_code = f"sh{code}"
    else:
        tencent_code = f"sz{code}"
    
    try:
        url = f"https://qt.gtimg.cn/q={tencent_code}"
        response = requests.get(url, timeout=10)
        data = response.text.split('~')
        
        if len(data) >= 30:
            pe = _num(data[28])
            pb = _num(data[29])
            return pe, pb
    except Exception as e:
        logger.warning(f"Failed to get PE/PB for {code}: {str(e)[:50]}")
    
    return None, None


def _candidate_fhps_report_dates() -> list[str]:
    """East Money dividend report dates YYYYMMDD, try from new to old"""
    y = date.today().year
    out: list[str] = []
    for yr in range(y, y - 4, -1):
        out.append(f"{yr}1231")
        out.append(f"{yr}0630")
    return out


def _calculate_recent_year_dividend(code: str) -> float | None:
    """
    Calculate dividend amount per share based on recent year's dividend records
    This matches the calculation method used by Sina Finance
    
    :param code: Pure stock code (6 digits)
    :return: Dividend amount per share (Yuan)
    """
    import akshare as ak
    from datetime import datetime, date, timedelta
    
    symbol = code
    
    try:
        df = ak.stock_history_dividend_detail(symbol=symbol)
        if df is None or df.empty:
            return None
        
        if '派息' not in df.columns or '除权除息日' not in df.columns:
            return None
        
        one_year_ago = (datetime.now() - timedelta(days=365)).date()
        total_div_per_10_share = 0.0
        
        for _, row in df.iterrows():
            ex_date = row.get('除权除息日')
            if pd.isna(ex_date):
                continue
            
            try:
                if isinstance(ex_date, str):
                    ex_date = datetime.strptime(ex_date, '%Y-%m-%d').date()
                elif isinstance(ex_date, datetime):
                    ex_date = ex_date.date()
                elif isinstance(ex_date, pd.Timestamp):
                    ex_date = ex_date.date()
                elif isinstance(ex_date, date):
                    pass
                else:
                    continue
            except:
                continue
            
            if ex_date >= one_year_ago:
                dividend = _num(row.get('派息'))
                if dividend is not None and dividend > 0:
                    total_div_per_10_share += dividend
        
        if total_div_per_10_share > 0:
            return total_div_per_10_share / 10.0
        
        return None
    except Exception as e:
        logger.debug(f"Failed to get dividend detail for {code}: {str(e)[:30]}")
        return None


def _load_dividend_yield_map_sync() -> dict[str, tuple[float | None, str | None, bool]]:
    """
    code -> (dividend amount per share, report period YYYYMMDD or None, is_direct_yield)
    
    is_direct_yield: False = value is dividend amount per share (need calculation)
    
    Priority: 
    1. Calculate from Sina stock_history_dividend_detail (most accurate, matches Sina Finance)
    2. Fallback to East Money stock_fhps_em
    3. Fallback to Sina stock_history_dividend (annual average)
    """
    import akshare as ak

    filled: dict[str, tuple[float | None, str | None, bool]] = {}

    try:
        df_em = ak.stock_fhps_em()
        if df_em is not None and not df_em.empty and "现金分红-现金分红比例" in df_em.columns:
            logger.info("Loading East Money stock_fhps_em for base dividend data")
            
            for _, row in df_em.iterrows():
                raw_code = row.get("代码")
                if raw_code is None or (isinstance(raw_code, float) and pd.isna(raw_code)):
                    continue
                code = str(raw_code).strip().zfill(6)
                if code in filled:
                    continue
                
                div_per_10_share = _num(row.get("现金分红-现金分红比例"))
                if div_per_10_share is None or div_per_10_share <= 0:
                    continue
                
                div_amount = div_per_10_share / 10.0
                filled[code] = (div_amount, None, False)
            
            logger.info(f"Got {len(filled)} dividend records from East Money")
    except Exception as e:
        logger.warning(f"East Money stock_fhps_em failed: {str(e)[:50]}")

    if not filled:
        try:
            df_sina = ak.stock_history_dividend()
            if df_sina is not None and not df_sina.empty and "年均股息" in df_sina.columns:
                logger.info("Fallback to Sina stock_history_dividend")
                
                for _, row in df_sina.iterrows():
                    raw = row.get("代码")
                    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
                        continue
                    code = str(raw).strip().zfill(6)
                    if not code or code in filled:
                        continue
                    val = _num(row.get("年均股息"))
                    if val is None or val <= 0:
                        continue
                    filled[code] = (val, None, False)
                
                logger.info(f"Got {len(filled)} dividend records from Sina stock_history_dividend")
        except Exception as e:
            logger.warning(f"Sina stock_history_dividend failed: {str(e)[:50]}")

    return filled


def _remove_market_prefix(code: str) -> str:
    """Remove market prefix from stock code (like sh/sz/bj), return pure number"""
    code = str(code).strip()
    if code.lower().startswith('sh') or code.lower().startswith('sz') or code.lower().startswith('bj'):
        return code[2:].zfill(6)
    return code.zfill(6)


def _load_pe_pb_map_sync() -> dict[str, tuple[float | None, float | None]]:
    """
    Get PE and PB data for individual stocks
    Returns: code -> (pe_dynamic, pb)
    Try multiple data sources, prioritize those with these fields
    """
    import akshare as ak
    import requests
    
    filled: dict[str, tuple[float | None, float | None]] = {}
    
    try:
        url = "https://qt.gtimg.cn/q="
        
        df = ak.stock_zh_a_spot()
        if df is not None and not df.empty:
            codes = []
            code_mapping = {}
            for _, row in df.iterrows():
                raw_code = row.get("代码")
                if raw_code is None:
                    continue
                code = str(raw_code).strip()
                code_lower = code.lower()
                
                if code_lower.startswith('sh'):
                    pure_code = code[2:].zfill(6)
                    tencent_code = f"sh{pure_code}"
                elif code_lower.startswith('sz'):
                    pure_code = code[2:].zfill(6)
                    tencent_code = f"sz{pure_code}"
                elif code_lower.startswith('bj'):
                    continue
                elif code.startswith('6'):
                    pure_code = code.zfill(6)
                    tencent_code = f"sh{pure_code}"
                else:
                    pure_code = code.zfill(6)
                    tencent_code = f"sz{pure_code}"
                
                codes.append(tencent_code)
                code_mapping[tencent_code] = pure_code
            
            batch_size = 60
            for i in range(0, len(codes), batch_size):
                batch = codes[i:i + batch_size]
                symbols = ','.join(batch)
                try:
                    response = requests.get(f"{url}{symbols}", timeout=15)
                    if response.status_code == 200:
                        lines = response.text.strip().split('\n')
                        for line in lines:
                            if not line:
                                continue
                            if '=' not in line:
                                continue
                            parts = line.split('=')
                            if len(parts) < 2:
                                continue
                            symbol = parts[0][2:]
                            
                            if symbol.lower() == 'pv_none_match':
                                continue
                            
                            data = parts[1].strip('"')
                            fields = data.split('~')
                            
                            if symbol in code_mapping:
                                code = code_mapping[symbol]
                            else:
                                if symbol.lower().startswith('sh'):
                                    code = symbol[2:].zfill(6)
                                elif symbol.lower().startswith('sz'):
                                    code = symbol[2:].zfill(6)
                                else:
                                    continue
                            
                            if code in filled:
                                continue
                            
                            pe = _num(fields[47]) if len(fields) > 47 else None
                            pb_val = _num(fields[48]) if len(fields) > 48 else None
                            
                            if pe is not None or pb_val is not None:
                                filled[code] = (pe, pb_val)
                    else:
                        logger.warning(f"Tencent interface status: {response.status_code}")
                        break
                except Exception as e:
                    logger.warning(f"Tencent batch request failed: {str(e)[:50]}")
                    break
        
        if filled:
            logger.info(f"Got {len(filled)} PE/PB records from Tencent interface")
            return filled
    except Exception as e:
        logger.warning(f"Tencent interface failed for PE/PB: {str(e)[:50]}")
    
    try:
        df = ak.stock_zh_valuation_comparison_em()
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                raw_code = row.get("代码")
                if raw_code is None or (isinstance(raw_code, float) and pd.isna(raw_code)):
                    continue
                code = str(raw_code).strip().zfill(6)
                if code in filled:
                    continue
                pe = _num(row.get("市盈率-TTM")) or _num(row.get("市盈率-动态"))
                pb_val = _num(row.get("市净率-MRQ")) or _num(row.get("市净率"))
                if pe is not None or pb_val is not None:
                    filled[code] = (pe, pb_val)
            logger.info(f"Got {len(filled)} PE/PB records from stock_zh_valuation_comparison_em")
            return filled
    except Exception as e:
        logger.warning(f"stock_zh_valuation_comparison_em failed for PE/PB: {str(e)[:50]}")
    
    try:
        df = ak.stock_zh_a_spot_em()
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                raw_code = row.get("代码")
                if raw_code is None or (isinstance(raw_code, float) and pd.isna(raw_code)):
                    continue
                code = str(raw_code).strip().zfill(6)
                if code in filled:
                    continue
                pe = _num(row.get("市盈率-动态")) or _num(row.get("市盈率"))
                pb_val = _num(row.get("市净率"))
                if pe is not None or pb_val is not None:
                    filled[code] = (pe, pb_val)
            logger.info(f"Got {len(filled)} PE/PB records from stock_zh_a_spot_em")
            return filled
    except Exception as e:
        logger.warning(f"stock_zh_a_spot_em failed for PE/PB: {str(e)[:50]}")
    
    logger.info(f"PE/PB data fetch complete, got {len(filled)} records")
    return filled


def _rows_from_dataframe(
    df: pd.DataFrame,
    dividend_by_code: dict[str, tuple[float | None, str | None, bool]],
    pe_pb_by_code: dict[str, tuple[float | None, float | None]] | None = None,
) -> list[AShareStockBasic]:
    """Parse DataFrame and build list of AShareStockBasic records"""
    rows: list[AShareStockBasic] = []
    for r in df.to_dict(orient="records"):
        raw_code = r.get("代码")
        if raw_code is None or (isinstance(raw_code, float) and pd.isna(raw_code)):
            continue
        code = str(raw_code).strip().zfill(6)
        name = r.get("名称")
        if name is None or (isinstance(name, float) and pd.isna(name)):
            name = ""
        else:
            name = str(name).strip()[:64]
        
        latest_price = _num(r.get("最新价"))
        
        dividend_code = _remove_market_prefix(code)
        
        recent_div_amount = _calculate_recent_year_dividend(dividend_code)
        
        if recent_div_amount is None:
            div_triple = dividend_by_code.get(dividend_code, (None, None, False))
            div_value, div_as_of, is_direct_yield = div_triple[0], div_triple[1], div_triple[2]
        else:
            div_value, div_as_of, is_direct_yield = recent_div_amount, None, False
        
        dividend_yield = None
        if div_value is not None and latest_price is not None and latest_price > 0:
            dividend_yield = (div_value / latest_price) * 100
        
        dividend_yield = _validate_dividend_yield(dividend_yield)
        
        pe_dynamic = None
        pb_val = None
        if pe_pb_by_code:
            query_code = _remove_market_prefix(code)
            pe_pb_pair = pe_pb_by_code.get(query_code)
            if pe_pb_pair:
                pe_dynamic, pb_val = pe_pb_pair
        
        if pe_dynamic is None:
            pe_dynamic = _num(r.get("市盈率-动态")) or _num(r.get("市盈率"))
        if pb_val is None:
            pb_val = _num(r.get("市净率"))

        rows.append(
            AShareStockBasic(
                code=code,
                name=name,
                board_label=_infer_board_label(code),
                dividend_yield=dividend_yield,
                dividend_yield_as_of=div_as_of,
                latest_price=latest_price,
                change_pct=_num(r.get("涨跌幅")),
                change_amount=_num(r.get("涨跌额")),
                volume=_num(r.get("成交量")),
                amount=_num(r.get("成交额")),
                amplitude=_num(r.get("振幅")),
                high=_num(r.get("最高")),
                low=_num(r.get("最低")),
                open_price=_num(r.get("今开")),
                prev_close=_num(r.get("昨收")),
                volume_ratio=_num(r.get("量比")),
                turnover_rate=_num(r.get("换手率")),
                pe_dynamic=pe_dynamic,
                pb=pb_val,
                total_market_cap=_num(r.get("总市值")),
                circulating_market_cap=_num(r.get("流通市值")),
                rise_speed=_num(r.get("涨速")),
                change_5min=_num(r.get("5分钟涨跌")),
                change_60d=_num(r.get("60日涨跌幅")),
                change_ytd=_num(r.get("年初至今涨跌幅")),
            )
        )
    return rows


async def sync_a_share_stock_basic_once() -> int:
    """
    Pull East Money A-share full market data and update/insert to a_share_stock_basic (Upsert)
    Based on unique constraint on code, update if exists, insert if not
    Returns processed count; logs error and returns 0 on failure
    """
    max_retries = 5
    base_delay = 5

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 3)
                logger.info(f"========== 重试第 {attempt + 1}/{max_retries} 次 ==========")
                logger.info(f"重试原因: 网络请求失败或数据获取异常")
                logger.info(f"等待 {delay:.1f} 秒后进行第 {attempt + 1} 次尝试...")
                await asyncio.sleep(delay)
            else:
                await asyncio.sleep(random.uniform(1, 3))

            df: pd.DataFrame = await asyncio.to_thread(_load_spot_dataframe_sync)
            dividend_map: dict[str, tuple[float | None, str | None, bool]] = await asyncio.to_thread(
                _load_dividend_yield_map_sync
            )
            pe_pb_map: dict[str, tuple[float | None, float | None]] = await asyncio.to_thread(
                _load_pe_pb_map_sync
            )
            if df is None or df.empty:
                logger.warning("A-share market data empty, skip storage")
                return 0
            records = _rows_from_dataframe(df, dividend_map, pe_pb_map)
            if not records:
                logger.warning("No valid records after parsing, skip storage")
                return 0

            async with async_session_maker() as session:
                chunk_size = 500
                for i in range(0, len(records), chunk_size):
                    chunk = records[i:i + chunk_size]
                    for record in chunk:
                        insert_stmt = mysql_insert(AShareStockBasic).values(
                            code=record.code,
                            name=record.name,
                            board_label=record.board_label,
                            dividend_yield=record.dividend_yield,
                            dividend_yield_as_of=record.dividend_yield_as_of,
                            latest_price=record.latest_price,
                            change_pct=record.change_pct,
                            change_amount=record.change_amount,
                            volume=record.volume,
                            amount=record.amount,
                            amplitude=record.amplitude,
                            high=record.high,
                            low=record.low,
                            open_price=record.open_price,
                            prev_close=record.prev_close,
                            volume_ratio=record.volume_ratio,
                            turnover_rate=record.turnover_rate,
                            pe_dynamic=record.pe_dynamic,
                            pb=record.pb,
                            total_market_cap=record.total_market_cap,
                            circulating_market_cap=record.circulating_market_cap,
                            rise_speed=record.rise_speed,
                            change_5min=record.change_5min,
                            change_60d=record.change_60d,
                            change_ytd=record.change_ytd,
                        )
                        on_conflict_stmt = insert_stmt.on_duplicate_key_update(
                            name=insert_stmt.inserted.name,
                            board_label=insert_stmt.inserted.board_label,
                            dividend_yield=insert_stmt.inserted.dividend_yield,
                            dividend_yield_as_of=insert_stmt.inserted.dividend_yield_as_of,
                            latest_price=insert_stmt.inserted.latest_price,
                            change_pct=insert_stmt.inserted.change_pct,
                            change_amount=insert_stmt.inserted.change_amount,
                            volume=insert_stmt.inserted.volume,
                            amount=insert_stmt.inserted.amount,
                            amplitude=insert_stmt.inserted.amplitude,
                            high=insert_stmt.inserted.high,
                            low=insert_stmt.inserted.low,
                            open_price=insert_stmt.inserted.open_price,
                            prev_close=insert_stmt.inserted.prev_close,
                            volume_ratio=insert_stmt.inserted.volume_ratio,
                            turnover_rate=insert_stmt.inserted.turnover_rate,
                            pe_dynamic=func.ifnull(insert_stmt.inserted.pe_dynamic, AShareStockBasic.pe_dynamic),
                            pb=func.ifnull(insert_stmt.inserted.pb, AShareStockBasic.pb),
                            total_market_cap=insert_stmt.inserted.total_market_cap,
                            circulating_market_cap=insert_stmt.inserted.circulating_market_cap,
                            rise_speed=insert_stmt.inserted.rise_speed,
                            change_5min=insert_stmt.inserted.change_5min,
                            change_60d=insert_stmt.inserted.change_60d,
                            change_ytd=insert_stmt.inserted.change_ytd,
                            updated_at=func.now(),
                        )
                        await session.execute(on_conflict_stmt)
                    await session.commit()
                    logger.info(f"Submitted batch {i // chunk_size + 1}, {min(i + chunk_size, len(records))}/{len(records)} records")

            logger.info("A-share basic info synced, total %s records", len(records))
            return len(records)
        except Exception as e:
            logger.error(f"---------- A-share basic info sync 第 {attempt + 1} 次尝试失败 ----------")
            logger.error(f"失败原因: {str(e)[:200]}")
            logger.error(f"剩余重试次数: {max_retries - attempt - 1}")
            if attempt == max_retries - 1:
                logger.exception("========== A-share basic info sync 所有重试均失败，放弃同步 ==========")
                return 0


async def run_a_share_stock_basic_sync_loop(interval_seconds: int) -> None:
    """
    Periodic sync: sleep for interval_seconds after each execution until task canceled
    """
    if interval_seconds < 1:
        logger.warning(
            "a_share_basic_sync_interval_seconds=%s invalid, fallback to 3600",
            interval_seconds,
        )
        interval_seconds = 3600

    sync_count = 0
    while True:
        try:
            sync_count += 1
            logger.info(f"=== Starting A-share basic info sync #{sync_count} ===")
            start_time = asyncio.get_event_loop().time()

            result = await sync_a_share_stock_basic_once()

            elapsed_time = asyncio.get_event_loop().time() - start_time
            if result > 0:
                logger.info(f"=== Sync #{sync_count} complete, updated {result} records, took {elapsed_time:.2f}s ===")
            else:
                logger.info(f"=== Sync #{sync_count} complete, no data updated, took {elapsed_time:.2f}s ===")

            logger.info(f"Next sync in {interval_seconds // 60} minutes")
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            logger.info("A-share basic info periodic sync stopped")
            raise
