"""
沪深京 A 股基本信息同步：通过 AKShare 东财接口分页拉取全市场，写入 a_share_stock_basic 表。
阻塞型 IO 与 pandas 在 asyncio.to_thread 中执行，避免阻塞 FastAPI 事件循环。
"""

from __future__ import annotations

import asyncio
import logging
import math
from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy import delete

from database import async_session_maker
from models import AShareStockBasic

logger = logging.getLogger(__name__)


def _infer_board_label(code: str) -> str:
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
    import akshare as ak

    return ak.stock_zh_a_spot_em()


def _candidate_fhps_report_dates() -> list[str]:
    """东财分红配送报告期 YYYYMMDD，从新到旧尝试。"""
    y = date.today().year
    out: list[str] = []
    for yr in range(y, y - 4, -1):
        out.append(f"{yr}1231")
        out.append(f"{yr}0630")
    return out


def _load_dividend_yield_map_sync() -> dict[str, tuple[float | None, str | None]]:
    """
    code -> (股息率%, 报告期或 None)。
    优先东财 stock_fhps_em「现金分红-股息率」；仍未覆盖的用新浪 stock_history_dividend「年均股息」。
    """
    import akshare as ak

    col_em = "现金分红-股息率"
    filled: dict[str, tuple[float | None, str | None]] = {}

    for report_date in _candidate_fhps_report_dates():
        try:
            df = ak.stock_fhps_em(date=report_date)
        except Exception:
            logger.debug("stock_fhps_em(%s) 不可用", report_date, exc_info=True)
            continue
        if df is None or df.empty or col_em not in df.columns:
            continue
        for _, row in df.iterrows():
            raw = row.get("代码")
            if raw is None or (isinstance(raw, float) and pd.isna(raw)):
                continue
            code = str(raw).strip().zfill(6)
            if not code or code in filled:
                continue
            val = _num(row.get(col_em))
            if val is None:
                continue
            filled[code] = (val, report_date)

    try:
        df_sina = ak.stock_history_dividend()
    except Exception:
        logger.debug("stock_history_dividend 不可用", exc_info=True)
        df_sina = None

    if df_sina is not None and not df_sina.empty and "年均股息" in df_sina.columns:
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

    return filled


def _rows_from_dataframe(
    df: pd.DataFrame,
    dividend_by_code: dict[str, tuple[float | None, str | None]],
) -> list[AShareStockBasic]:
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
        div_pair = dividend_by_code.get(code, (None, None))
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
    拉取东财 A 股全市场行情并覆盖写入 a_share_stock_basic。
    返回写入条数；失败时记录日志并返回 0。
    """
    try:
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
            await session.execute(delete(AShareStockBasic))
            chunk = 500
            for i in range(0, len(records), chunk):
                session.add_all(records[i : i + chunk])
            await session.commit()

        logger.info("A 股基本信息已同步，共 %s 条", len(records))
        return len(records)
    except Exception:
        logger.exception("A 股基本信息同步失败")
        return 0


async def run_a_share_stock_basic_sync_loop(interval_seconds: int) -> None:
    """
    周期性同步：每次执行完后休眠 interval_seconds，直至任务被取消。
    """
    if interval_seconds < 1:
        logger.warning(
            "a_share_basic_sync_interval_seconds=%s 无效，已回退为 60",
            interval_seconds,
        )
        interval_seconds = 60
    while True:
        try:
            await sync_a_share_stock_basic_once()
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            logger.info("A 股基本信息定时同步已停止")
            raise
