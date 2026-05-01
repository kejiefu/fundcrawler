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
    """
    同步加载 A 股实时行情数据
    优先使用东方财富接口（包含市盈率、市净率等更多字段），失败则回退到新浪接口
    """
    import akshare as ak
    
    # 优先尝试东方财富接口，包含市盈率和市净率数据
    try:
        df = ak.stock_zh_a_spot_em()
        if df is not None and not df.empty:
            logger.info("使用东方财富接口获取 A 股行情数据")
            return df
    except Exception as e:
        logger.warning(f"东方财富接口调用失败，将回退到新浪接口: {str(e)[:50]}")
    
    # 回退到新浪接口
    logger.info("使用新浪接口获取 A 股行情数据")
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


def _load_pe_pb_map_sync() -> dict[str, tuple[float | None, float | None]]:
    """
    获取个股市盈率和市净率数据
    返回: code -> (pe_dynamic, pb)
    尝试从多个数据源获取，优先使用包含这些字段的接口
    """
    import akshare as ak
    import requests
    
    filled: dict[str, tuple[float | None, float | None]] = {}
    
    # 优先尝试腾讯股票接口获取市盈率和市净率数据（无需登录）
    try:
        # 腾讯股票接口，支持批量查询，格式为 sh600000,sz000001
        # 注意：腾讯接口仅支持沪市(sh)和深市(sz)股票，不支持北交所(bj)股票
        url = "https://qt.gtimg.cn/q="
        
        # 从新浪接口获取股票列表，用于构建腾讯接口请求
        df = ak.stock_zh_a_spot()
        if df is not None and not df.empty:
            codes = []
            code_mapping = {}  # 记录原始代码到腾讯格式代码的映射
            for _, row in df.iterrows():
                raw_code = row.get("代码")
                if raw_code is None:
                    continue
                code = str(raw_code).strip()
                code_lower = code.lower()
                
                # 提取纯数字代码用于后续匹配
                if code_lower.startswith('sh'):
                    pure_code = code[2:].zfill(6)
                    tencent_code = f"sh{pure_code}"
                elif code_lower.startswith('sz'):
                    pure_code = code[2:].zfill(6)
                    tencent_code = f"sz{pure_code}"
                elif code_lower.startswith('bj'):
                    # 北交所股票：腾讯接口不支持，跳过
                    continue
                elif code.startswith('6'):
                    pure_code = code.zfill(6)
                    tencent_code = f"sh{pure_code}"
                else:
                    pure_code = code.zfill(6)
                    tencent_code = f"sz{pure_code}"
                
                codes.append(tencent_code)
                code_mapping[tencent_code] = pure_code
            
            # 分批请求，每批最多60个股票
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
                            # 解析格式: v_sh600000="1~浦发银行~600000~..."
                            line = line.strip()
                            if '=' not in line:
                                continue
                            parts = line.split('=')
                            if len(parts) < 2:
                                continue
                            symbol = parts[0][2:]  # 去掉 v_ 前缀
                            
                            # 跳过未匹配的股票（如北交所股票）
                            if symbol.lower() == 'pv_none_match':
                                continue
                            
                            data = parts[1].strip('"')
                            fields = data.split('~')
                            
                            # 使用 code_mapping 获取纯数字代码
                            if symbol in code_mapping:
                                code = code_mapping[symbol]
                            else:
                                # 降级处理：直接从 symbol 提取
                                if symbol.lower().startswith('sh'):
                                    code = symbol[2:].zfill(6)
                                elif symbol.lower().startswith('sz'):
                                    code = symbol[2:].zfill(6)
                                else:
                                    continue
                            
                            if code in filled:
                                continue
                            
                            # 腾讯接口字段：47=市盈率, 48=市净率
                            pe = _num(fields[47]) if len(fields) > 47 else None
                            pb_val = _num(fields[48]) if len(fields) > 48 else None
                            
                            if pe is not None or pb_val is not None:
                                filled[code] = (pe, pb_val)
                    else:
                        logger.warning(f"腾讯接口返回状态码: {response.status_code}")
                        break
                except Exception as e:
                    logger.warning(f"腾讯接口批量请求失败: {str(e)[:50]}")
                    break
        
        if filled:
            logger.info(f"从腾讯接口获取到 {len(filled)} 条市盈率/市净率数据")
            return filled
    except Exception as e:
        logger.warning(f"腾讯接口获取市盈率/市净率失败: {str(e)[:50]}")
    
    # 尝试东方财富估值对比接口（包含市盈率和市净率）
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
                pe = _num(row.get("市盈率-TTM")) or _num(row.get("市盈率-25E"))
                pb_val = _num(row.get("市净率-MRQ")) or _num(row.get("市净率-24A"))
                if pe is not None or pb_val is not None:
                    filled[code] = (pe, pb_val)
            logger.info(f"从 stock_zh_valuation_comparison_em 获取到 {len(filled)} 条市盈率/市净率数据")
            return filled
    except Exception as e:
        logger.warning(f"stock_zh_valuation_comparison_em 获取市盈率/市净率失败: {str(e)[:50]}")
    
    # 尝试东方财富实时行情接口（包含市盈率和市净率）
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
                pe = _num(row.get("市盈率"))
                pb_val = _num(row.get("市净率"))
                if pe is not None or pb_val is not None:
                    filled[code] = (pe, pb_val)
            logger.info(f"从 stock_zh_a_spot_em 获取到 {len(filled)} 条市盈率/市净率数据")
            return filled
    except Exception as e:
        logger.warning(f"stock_zh_a_spot_em 获取市盈率/市净率失败: {str(e)[:50]}")
    
    logger.info(f"市盈率/市净率数据获取完成，共 {len(filled)} 条")
    return filled


def _rows_from_dataframe(
    df: pd.DataFrame,
    dividend_by_code: dict[str, tuple[float | None, str | None]],
    pe_pb_by_code: dict[str, tuple[float | None, float | None]] | None = None,
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
        
        # 优先从额外数据源获取市盈率和市净率，其次从主数据源获取
        pe_dynamic = None
        pb_val = None
        if pe_pb_by_code:
            # 使用移除前缀后的代码查询市盈率和市净率
            query_code = _remove_market_prefix(code)
            pe_pb_pair = pe_pb_by_code.get(query_code)
            if pe_pb_pair:
                pe_dynamic, pb_val = pe_pb_pair
        
        # 如果额外数据源没有，尝试从主数据源获取
        if pe_dynamic is None:
            pe_dynamic = _num(r.get("市盈率-动态")) or _num(r.get("市盈率"))
        if pb_val is None:
            pb_val = _num(r.get("市净率"))

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
            pe_pb_map: dict[str, tuple[float | None, float | None]] = await asyncio.to_thread(
                _load_pe_pb_map_sync
            )
            if df is None or df.empty:
                logger.warning("A 股行情数据为空，跳过入库")
                return 0
            records = _rows_from_dataframe(df, dividend_map, pe_pb_map)
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
                            # 只有当新值不为空时才更新市盈率和市净率，保持已有数据
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
