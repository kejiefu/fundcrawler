"""
沪深京 A 股基本信息同步：通过 AKShare 新浪接口分页拉取全市场，写入 a_share_stock_basic 表。
阻塞型 IO 与 pandas 在 asyncio.to_thread 中执行，避免阻塞事件循环。
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
    """根据证券代码推断所属交易所/板块"""
    c = str(code).strip().zfill(6)
    if len(c) < 6:
        return "其他"
    p2, p3 = c[:2], c[:3]
    if p2 in ("83", "87", "88", "92") or p3 == "430" or (p3 == "920"):
        return "北交所"
    if p3 in ("688", "689"):
        return "科创板"
    if p2 == "60":
        return "沪市主板"
    if p3 in ("000", "001", "002", "003"):
        return "深市主板"
    if p3 in ("300", "301"):
        return "创业板"
    return "其他"


def _num(v: Any) -> float | None:
    """将值转换为浮点数，None/NaN 返回 None"""
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


def _load_spot_dataframe_sync() -> pd.DataFrame:
    """同步加载 A 股实时行情数据"""
    import akshare as ak
    return ak.stock_zh_a_spot()


def _candidate_fhps_report_dates() -> list[str]:
    """东财分红配送报告期 YYYYMMDD，从新到旧尝试"""
    y = date.today().year
    out: list[str] = []
    for yr in range(y, y - 4, -1):
        out.append(f"{yr}1231")
        out.append(f"{yr}0630")
    return out


def _load_dividend_yield_map_sync() -> dict[str, tuple[float | None, str | None]]:
    """
    code -> (股息率%, 报告期或 None)
    使用新浪 stock_history_dividend「年均股息」作为股息率数据
    """
    import akshare as ak

    filled: dict[str, tuple[float | None, str | None]] = {}

    try:
        df_sina = ak.stock_history_dividend()
    except Exception as e:
        logger.warning("stock_history_dividend 不可用: %s", str(e)[:50])
        return filled

    if df_sina is None or df_sina.empty or "年均股息" not in df_sina.columns:
        logger.warning("stock_history_dividend 返回空数据或缺少年均股息列")
        return filled

    for _, row in df_sina.iterrows():
        raw = row.get("代码")
        if raw is None or (isinstance(raw, float) and pd.isna(raw)):
            continue
        code = str(raw).strip().zfill(6)
        if not code or code in filled:
            continue
        val = _num(row.get("年均股息"))
        if val is None:
            continue
        filled[code] = (val, None)

    logger.info(f"从 stock_history_dividend 获取到 {len(filled)} 条股息率数据")
    return filled


def _remove_market_prefix(code: str) -> str:
    """移除股票代码的市场前缀（如 sh/sz/bj），返回纯数字代码"""
    code = str(code).strip()
    if code.lower().startswith('sh') or code.lower().startswith('sz') or code.lower().startswith('bj'):
        return code[2:].zfill(6)
    return code.zfill(6)


def _rows_from_dataframe(
    df: pd.DataFrame,
    dividend_by_code: dict[str, tuple[float | None, str | None]],
) -> list[AShareStockBasic]:
    """从 DataFrame 解析并构建 AShareStockBasic 记录列表"""
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
        dividend_code = _remove_market_prefix(code)
        div_pair = dividend_by_code.get(dividend_code, (None, None))
        div_yield, div_as_of = div_pair[0], div_pair[1]

        rows.append(
            AShareStockBasic(
                code=code,
                name=name,
                board_label=_infer_board_label(code),
                dividend_yield=div_yield,
                dividend_yield_as_of=div_as_of,
                latest_price=_num(r.get("最新价")),
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
                pe_dynamic=_num(r.get("市盈率-动态")),
                pb=_num(r.get("市净率")),
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
    拉取东财 A 股全市场行情并更新/插入 a_share_stock_basic（Upsert）
    基于证券代码(code)唯一约束，存在则更新，不存在则插入
    返回处理条数；失败时记录日志并返回 0
    """
    max_retries = 3
    base_delay = 5

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 3)
                logger.info(f"第 {attempt + 1} 次重试，等待 {delay:.1f} 秒...")
                await asyncio.sleep(delay)
            else:
                await asyncio.sleep(random.uniform(1, 3))

            df: pd.DataFrame = await asyncio.to_thread(_load_spot_dataframe_sync)
            dividend_map: dict[str, tuple[float | None, str | None]] = await asyncio.to_thread(
                _load_dividend_yield_map_sync
            )
            if df is None or df.empty:
                logger.warning("A 股行情数据为空，跳过入库")
                return 0
            records = _rows_from_dataframe(df, dividend_map)
            if not records:
                logger.warning("解析后无有效记录，跳过入库")
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
                            pe_dynamic=insert_stmt.inserted.pe_dynamic,
                            pb=insert_stmt.inserted.pb,
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
                    logger.info(f"已提交第 {i // chunk_size + 1} 批数据，{min(i + chunk_size, len(records))}/{len(records)} 条")

            logger.info("A 股基本信息已同步，共 %s 条", len(records))
            return len(records)
        except Exception as e:
            logger.warning(f"A 股基本信息同步第 {attempt + 1} 次失败: {str(e)[:100]}")
            if attempt == max_retries - 1:
                logger.exception("A 股基本信息同步最终失败")
                return 0


async def run_a_share_stock_basic_sync_loop(interval_seconds: int) -> None:
    """
    周期性同步：每次执行完后休眠 interval_seconds，直至任务被取消
    """
    if interval_seconds < 1:
        logger.warning(
            "a_share_basic_sync_interval_seconds=%s 无效，已回退为 60",
            interval_seconds,
        )
        interval_seconds = 60

    sync_count = 0
    while True:
        try:
            sync_count += 1
            logger.info(f"=== 开始第 {sync_count} 次 A 股基本信息同步 ===")
            start_time = asyncio.get_event_loop().time()

            result = await sync_a_share_stock_basic_once()

            elapsed_time = asyncio.get_event_loop().time() - start_time
            if result > 0:
                logger.info(f"=== 第 {sync_count} 次同步完成，更新 {result} 条数据，耗时 {elapsed_time:.2f} 秒 ===")
            else:
                logger.info(f"=== 第 {sync_count} 次同步完成，未更新数据，耗时 {elapsed_time:.2f} 秒 ===")

            logger.info(f"下次同步将在 {interval_seconds // 60} 分钟后进行")
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            logger.info("A 股基本信息定时同步已停止")
            raise
