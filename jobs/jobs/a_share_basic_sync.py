"""
A-share basic info sync: pull full market via AKShare interface, 
write to a_share_stock_basic table
Blocking IO (pandas) runs in asyncio.to_thread to avoid blocking event loop
Dividend data is read from database (populated by dividend_sync task)
"""

from __future__ import annotations

import asyncio
import logging
import math
import random
from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd
from sqlalchemy import func
from sqlalchemy.dialects.mysql import insert as mysql_insert

from db.database import async_session_maker
from db.models import AShareStockBasic, AShareDividendDetail
from utils.sync_progress import (
    create_sync_progress,
    get_sync_progress,
    complete_sync_progress,
    fail_sync_progress,
)

logger = logging.getLogger(__name__)

TASK_NAME = "a_share_basic"


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


def _format_market_cap(value: float | None) -> float | None:
    """格式化市值数据，四舍五入到2位小数，匹配数据库 Numeric(22,2) 字段精度"""
    if value is None:
        return None
    try:
        value = float(value)
        if math.isnan(value) or math.isinf(value):
            return None
        return round(value, 2)
    except (TypeError, ValueError):
        return None


def _validate_dividend_yield(value: float | None) -> float | None:
    """校验股息率值，过滤异常数据
    
    A股合理股息率通常在 0%~15%，极端情况下不超过 20%
    超过 20% 通常意味着数据计算错误（如累加了全部历史分红）
    """
    if value is None:
        return None
    
    try:
        value = float(value)
        if math.isnan(value) or math.isinf(value):
            return None
        
        max_yield = 20.0  # A股股息率极少超过20%，超过则标记为异常
        min_yield = 0.0   # 股息率不应为负数
        
        if value > max_yield or value < min_yield:
            logger.warning(
                f"股息率 {value:.4f}% 超出合理范围 [{min_yield}%, {max_yield}%]，"
                f"标记为 None（可能数据计算有误）"
            )
            return None
        
        return round(value, 4)
    except (TypeError, ValueError):
        return None


_spot_cache: dict = {"df": None, "timestamp": 0}
_SPOT_CACHE_TTL = 300


def _get_cached_spot_dataframe() -> pd.DataFrame | None:
    import time
    current_time = time.time()
    if _spot_cache["df"] is not None and (current_time - _spot_cache["timestamp"]) < _SPOT_CACHE_TTL:
        return _spot_cache["df"]
    df = _load_spot_dataframe_sync()
    if df is not None and not df.empty:
        _spot_cache["df"] = df
        _spot_cache["timestamp"] = current_time
        logger.info(f"Spot data cached, next refresh after {_SPOT_CACHE_TTL}s")
    return df


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
    Get realtime data for a single stock (optimized: use cached spot data)
    :param code: Pure stock code (6 digits)
    :return: Dictionary with stock data or None
    """
    code = str(code).strip().zfill(6)

    df = _get_cached_spot_dataframe()
    if df is not None and not df.empty:
        df['代码'] = df['代码'].astype(str).str.zfill(6)
        row = df[df['代码'] == code]
        if not row.empty:
            return row.iloc[0].to_dict()

    return None


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


def _remove_market_prefix(code: str) -> str:
    """Remove market prefix from stock code (like sh/sz/bj), return pure number"""
    code = str(code).strip()
    if code.lower().startswith('sh') or code.lower().startswith('sz') or code.lower().startswith('bj'):
        return code[2:].zfill(6)
    return code.zfill(6)


def _load_tencent_valuation_map_sync() -> dict[str, tuple[float | None, float | None, float | None, float | None]]:
    """
    批量从腾讯接口一次性获取 PE/PB/总市值/流通市值，避免重复请求
    Returns: code -> (pe_dynamic, pb, total_market_cap, circulating_market_cap)
      - total_market_cap / circulating_market_cap 已从"亿"转换为"元"
    """
    import akshare as ak
    import requests

    result: dict[str, tuple[float | None, float | None, float | None, float | None]] = {}
    url = "https://qt.gtimg.cn/q="

    try:
        df = ak.stock_zh_a_spot()
        if df is None or df.empty:
            return result

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

        if not codes:
            return result

        batch_size = 60
        for i in range(0, len(codes), batch_size):
            batch = codes[i:i + batch_size]
            full_url = url + ",".join(batch)

            try:
                response = requests.get(full_url, timeout=30)
                if response.status_code != 200:
                    logger.warning(f"腾讯接口响应异常，状态码: {response.status_code}")
                    break

                lines = response.text.split(";\n")
                for line in lines:
                    if not line.strip():
                        continue
                    parts = line.split('~')

                    tencent_code_raw = parts[0]
                    tencent_code = tencent_code_raw.replace('v_sz', 'sz').replace('v_sh', 'sh')
                    if '=' in tencent_code:
                        tencent_code = tencent_code.split('=')[0]
                    pure_code = code_mapping.get(tencent_code)
                    if not pure_code:
                        continue

                    pe = _num(parts[28]) if len(parts) > 28 else None
                    pb_val = _num(parts[29]) if len(parts) > 29 else None
                    total_cap = _num(parts[44]) if len(parts) > 44 else None
                    circ_cap = _num(parts[45]) if len(parts) > 45 else None

                    if total_cap is not None:
                        total_cap = total_cap * 100000000
                    if circ_cap is not None:
                        circ_cap = circ_cap * 100000000

                    result[pure_code] = (pe, pb_val, total_cap, circ_cap)
            except Exception as e:
                logger.warning(f"腾讯接口批量请求失败: {str(e)[:50]}")
                break

        logger.info(f"从腾讯接口获取到 {len(result)} 条估值数据")
        return result
    except Exception as e:
        logger.warning(f"腾讯接口调用失败: {str(e)[:50]}")

    return result


async def _load_dividend_yield_map() -> dict[str, tuple[float | None, str | None, bool]]:
    """
    从数据库读取分红数据（从新表 AShareDividendDetail 读取）
    
    code -> (dividend amount per share, report period YYYYMMDD or None, is_direct_yield)
    
    is_direct_yield: False = value is dividend amount per share (need calculation)
    
    只累加最近365天内除权除息的实施分红，避免累加全部历史数据导致股息率虚高
    """
    from datetime import timedelta

    one_year_ago_str = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
    filled: dict[str, tuple[float | None, str | None, bool]] = {}
    
    async with async_session_maker() as session:
        # 从新表 AShareDividendDetail 获取分红数据（仅实施状态、有派息、有除权除息日）
        result = await session.execute(
            AShareDividendDetail.__table__.select()
            .where(AShareDividendDetail.dividend.isnot(None))
            .where(AShareDividendDetail.dividend > 0)
            .where(AShareDividendDetail.progress == '实施')
            .where(AShareDividendDetail.ex_dividend_date.isnot(None))
        )
        
        # 按股票代码分组，只累加最近365天内除权除息的实施分红
        dividend_by_code: dict[str, float] = {}
        latest_date_by_code: dict[str, str] = {}
        skipped_out_of_range = 0
        
        for row in result:
            ex_date = row.ex_dividend_date
            if ex_date is None or ex_date < one_year_ago_str:
                skipped_out_of_range += 1
                continue
            
            code = row.code
            dividend = float(row.dividend) if row.dividend else 0
            
            if code not in dividend_by_code:
                dividend_by_code[code] = 0
                latest_date_by_code[code] = ex_date
            else:
                dividend_by_code[code] += dividend
                if ex_date and ex_date > latest_date_by_code.get(code, ''):
                    latest_date_by_code[code] = ex_date
        
        # 转换为每股分红
        for code, total_dividend in dividend_by_code.items():
            if total_dividend > 0:
                dividend_per_share = total_dividend / 10.0  # 每10股分红转每股
                filled[code] = (dividend_per_share, latest_date_by_code.get(code), False)
    
    logger.info(
        f"Loaded {len(filled)} dividend records from AShareDividendDetail "
        f"(skipped {skipped_out_of_range} records out of 365-day range)"
    )
    return filled


def _rows_from_dataframe(
    df: pd.DataFrame,
    dividend_by_code: dict[str, tuple[float | None, str | None, bool]],
    tencent_valuation: dict[str, tuple[float | None, float | None, float | None, float | None]] | None = None,
) -> list[AShareStockBasic]:
    """解析DataFrame，合并各数据源构建AShareStockBasic记录列表
    tencent_valuation: code -> (pe, pb, total_market_cap, circulating_market_cap)
    """
    rows: list[AShareStockBasic] = []
    for r in df.to_dict(orient="records"):
        raw_code = r.get("代码")
        if raw_code is None or (isinstance(raw_code, float) and pd.isna(raw_code)):
            continue
        code = _remove_market_prefix(raw_code)
        name = r.get("名称")
        if name is None or (isinstance(name, float) and pd.isna(name)):
            name = ""
        else:
            name = str(name).strip()[:64]

        latest_price = _num(r.get("最新价"))

        pe_dynamic = None
        pb_val = None
        total_market_cap = _num(r.get("总市值"))
        circulating_market_cap = _num(r.get("流通市值"))

        if tencent_valuation:
            valuation = tencent_valuation.get(code)
            if valuation:
                pe_dynamic, pb_val, cap_total, cap_circ = valuation
                if cap_total is not None:
                    total_market_cap = cap_total
                if cap_circ is not None:
                    circulating_market_cap = cap_circ

        dividend_yield = None
        div_as_of = None

        div_triple = dividend_by_code.get(code, (None, None, False))
        if div_triple[0] is not None and latest_price is not None and latest_price > 0:
            dividend_yield = (div_triple[0] / latest_price) * 100
            dividend_yield = _validate_dividend_yield(dividend_yield)
            div_as_of = div_triple[1]

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
                total_market_cap=total_market_cap,
                circulating_market_cap=circulating_market_cap,
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
    batch_id: str | None = None
    start_time = datetime.now()

    logger.info("=" * 60)
    logger.info(f"【A股基本信息同步任务】开始执行")
    logger.info(f"【当前时间】{start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    running_progress = await get_sync_progress(TASK_NAME)
    if running_progress:
        _, _, existing_batch_id = running_progress
        logger.warning(f"【跳过】发现正在运行的同步任务，batch_id: {existing_batch_id}")
        logger.info("=" * 60)
        return 0

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 3)
                logger.info(f"【重试】第 {attempt + 1}/{max_retries} 次尝试")
                logger.info(f"【等待】{delay:.1f} 秒后继续...")
                await asyncio.sleep(delay)
            else:
                await asyncio.sleep(random.uniform(1, 3))

            logger.info("【步骤1/4】开始加载A股实时行情数据...")
            df: pd.DataFrame = await asyncio.to_thread(_load_spot_dataframe_sync)
            if df is None or df.empty:
                logger.warning("【数据为空】A股行情数据为空，跳过本次同步")
                logger.info("=" * 60)
                return 0
            logger.info(f"【步骤1/4完成】成功加载 {len(df)} 条A股行情数据")

            logger.info("【步骤2/4】开始加载分红数据...")
            dividend_map: dict[str, tuple[float | None, str | None, bool]] = await _load_dividend_yield_map()
            logger.info(f"【步骤2/4完成】成功加载 {len(dividend_map)} 条分红记录")

            logger.info("【步骤3/4】开始加载腾讯估值数据...")
            tencent_valuation_map: dict[str, tuple[float | None, float | None, float | None, float | None]] = await asyncio.to_thread(
                _load_tencent_valuation_map_sync
            )
            logger.info(f"【步骤3/4完成】成功加载 {len(tencent_valuation_map)} 条估值数据")

            logger.info("【步骤4/4】开始解析数据并写入数据库...")
            records = _rows_from_dataframe(df, dividend_map, tencent_valuation_map)
            if not records:
                logger.warning("【解析失败】没有有效的记录，跳过存储")
                logger.info("=" * 60)
                return 0
            logger.info(f"【解析完成】成功解析 {len(records)} 条有效记录")

            batch_id = await create_sync_progress(TASK_NAME, len(records))
            logger.info(f"【进度记录】已创建同步进度记录，batch_id: {batch_id}")

            logger.info(f"【入库开始】准备将 {len(records)} 条记录写入数据库，分批次处理...")
            async with async_session_maker() as session:
                chunk_size = 500
                total_batches = (len(records) + chunk_size - 1) // chunk_size
                processed_count = 0
                
                for i in range(0, len(records), chunk_size):
                    chunk = records[i:i + chunk_size]
                    batch_num = i // chunk_size + 1
                    logger.info(f"【批次处理】正在处理第 {batch_num}/{total_batches} 批次，共 {len(chunk)} 条记录")
                    
                    precise_count = 0
                    for record in chunk:
                        current_dividend_yield = record.dividend_yield
                        
                        need_precise_calc = False
                        if record.name and ("ST" not in record.name and "*ST" not in record.name and "PT" not in record.name and "退市" not in record.name):
                            if record.total_market_cap:
                                if record.total_market_cap >= 40000000000:
                                    need_precise_calc = True
                            else:
                                need_precise_calc = True
                        
                        if need_precise_calc and record.latest_price and record.latest_price > 0:
                            precise_div = await asyncio.to_thread(_calculate_recent_year_dividend, record.code)
                            if precise_div is not None:
                                latest_price_float = float(record.latest_price) if hasattr(record.latest_price, '__float__') else float(record.latest_price)
                                current_dividend_yield = (precise_div / latest_price_float) * 100
                                current_dividend_yield = _validate_dividend_yield(current_dividend_yield)
                                precise_count += 1
                        
                        insert_stmt = mysql_insert(AShareStockBasic).values(
                            code=record.code,
                            name=record.name,
                            board_label=record.board_label,
                            dividend_yield=current_dividend_yield,
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
                        processed_count += 1
                    
                    await session.commit()
                    logger.info(f"【批次完成】第 {batch_num}/{total_batches} 批次提交成功，累计处理 {processed_count}/{len(records)} 条")
                    if precise_count > 0:
                        logger.info(f"【精确计算】本批次有 {precise_count} 只股票进行了精确股息率计算")

            if batch_id:
                await complete_sync_progress(TASK_NAME, batch_id)
                logger.info(f"【进度更新】同步进度已标记为完成")

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"【任务完成】A股基本信息同步成功！")
            logger.info(f"【处理结果】共处理 {len(records)} 条记录")
            logger.info(f"【耗时统计】总耗时 {duration:.2f} 秒")
            logger.info(f"【结束时间】{end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 60)
            
            return len(records)
        except Exception as e:
            if batch_id:
                await fail_sync_progress(TASK_NAME, batch_id)
                logger.info(f"【进度更新】同步进度已标记为失败")
            
            logger.error(f"【任务失败】第 {attempt + 1} 次尝试失败")
            logger.error(f"【失败原因】{str(e)[:200]}")
            logger.error(f"【剩余重试】{max_retries - attempt - 1} 次")
            if attempt == max_retries - 1:
                logger.error("【放弃同步】所有重试均失败，任务终止")
                logger.info("=" * 60)
                return 0


async def run_a_share_stock_basic_sync_loop(interval_seconds: int) -> None:
    """
    Run A-share basic info sync periodically
    :param interval_seconds: Sync interval in seconds
    """
    interval_minutes = interval_seconds / 60
    logger.info("=" * 60)
    logger.info(f"【定时任务启动】A股基本信息同步循环")
    logger.info(f"【同步间隔】{interval_seconds} 秒 ({interval_minutes:.1f} 分钟)")
    logger.info("=" * 60)
    
    while True:
        try:
            sync_num = _get_sync_count()
            logger.info(f"【第 {sync_num} 次同步】即将开始...")
            count = await sync_a_share_stock_basic_once()
            
            next_run = datetime.now() + timedelta(seconds=interval_seconds)
            logger.info(f"【下次执行】预计 {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("-" * 60)
        except Exception as e:
            logger.error(f"【循环异常】{str(e)[:200]}")
            logger.info("-" * 60)
        
        logger.info(f"【等待中】下次同步将在 {interval_minutes:.1f} 分钟后进行...")
        await asyncio.sleep(interval_seconds)


_sync_counter = 0

def _get_sync_count() -> int:
    """Get and increment sync counter"""
    global _sync_counter
    _sync_counter += 1
    return _sync_counter