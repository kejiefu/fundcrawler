import asyncio
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Optional
import logging
from sqlalchemy.dialects.mysql import insert as mysql_insert
from database import get_db, async_session_maker
from models import AShareStockBasic, AShareKline, AShareIndicator, AShareFinancialReport
from schemas import StockBasicResponse, StockListResponse, KlineResponse, IndicatorResponse, KlineIndicatorResponse, KlineListResponse, FinancialReportResponse, FinancialReportListResponse
from auth import get_current_active_user
from core.kline_sync_core import (
    PERIOD_MAP, _convert_code, is_valid_stock_code,
    load_kline_data_from_akshare, parse_kline_data, get_sync_start_date
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stocks", tags=["Stocks"])

@router.get("/", response_model=StockListResponse, summary="Get stock list")
async def get_stocks(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    board_label: Optional[str] = None,
    search: Optional[str] = None,
    dividend_yield_min: Optional[float] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> StockListResponse:
    """Get stock list with pagination, board filtering, search, and dividend yield filtering"""
    query = select(AShareStockBasic)

    if board_label:
        query = query.where(AShareStockBasic.board_label == board_label)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                AShareStockBasic.code.like(search_pattern),
                AShareStockBasic.name.like(search_pattern)
            )
        )
    else:
        query = query.where(
            ~AShareStockBasic.name.like("%ST%"),
            ~AShareStockBasic.name.like("%*ST%"),
            ~AShareStockBasic.name.like("%退市%")
        )

    if dividend_yield_min is not None:
        query = query.where(AShareStockBasic.dividend_yield > dividend_yield_min)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(AShareStockBasic.code).offset(skip).limit(limit)
    result = await db.execute(query)
    stocks = result.scalars().all()

    page = (skip // limit) + 1 if limit > 0 else 1

    return StockListResponse(
        total=total,
        items=[StockBasicResponse.model_validate(s) for s in stocks],
        page=page,
        page_size=limit
    )

@router.get("/boards", summary="Get all board list")
async def get_boards(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> List[str]:
    """Get all board list"""
    query = select(AShareStockBasic.board_label).distinct().where(
        AShareStockBasic.board_label.isnot(None)
    )
    result = await db.execute(query)
    boards = [row[0] for row in result.fetchall() if row[0]]
    return sorted(boards)

def normalize_stock_code(code: str) -> str:
    """Normalize stock code - handles both prefixed (sh/sz/bj) and unprefixed codes"""
    code = str(code).strip()
    if code.lower().startswith('sh') or code.lower().startswith('sz') or code.lower().startswith('bj'):
        return code
    elif code.startswith('6') or code.startswith('9'):
        return f"sh{code}"
    elif code.startswith('8') or code.startswith('4'):
        return f"bj{code}"
    else:
        return f"sz{code}"


def extract_pure_code(code: str) -> str:
    """Extract pure numeric code from prefixed code (e.g., sh600519 -> 600519)"""
    code = str(code).strip().lower()
    if code.startswith('sh'):
        return code[2:]
    elif code.startswith('sz'):
        return code[2:]
    elif code.startswith('bj'):
        return code[2:]
    return code


@router.get("/{code}", response_model=StockBasicResponse, summary="Get single stock info")
async def get_stock(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> StockBasicResponse:
    """Get stock detailed info by code"""
    pure_code = extract_pure_code(code)

    query = select(AShareStockBasic).where(AShareStockBasic.code == pure_code)
    result = await db.execute(query)
    stock = result.scalar_one_or_none()

    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    return StockBasicResponse.model_validate(stock)


@router.get("/{code}/kline", response_model=KlineListResponse, summary="Get stock kline data with indicators")
async def get_stock_kline(
    code: str,
    period: int = Query(1, ge=1, le=4, description="周期类型(1=日线,2=周线,3=月线,4=年线)"),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> KlineListResponse:
    """Get stock kline data with KDJ and RSI indicators"""
    pure_code = extract_pure_code(code)

    kline_query = select(AShareKline).where(
        or_(
            AShareKline.code == code,
            AShareKline.code == pure_code
        ),
        AShareKline.period == period
    ).order_by(AShareKline.trade_date.desc()).limit(limit)

    kline_result = await db.execute(kline_query)
    klines = kline_result.scalars().all()

    if not klines:
        return KlineListResponse(
            total=0,
            items=[],
            code=code,
            period=period
        )

    trade_dates = [k.trade_date for k in klines]
    indicator_query = select(AShareIndicator).where(
        or_(
            AShareIndicator.code == code,
            AShareIndicator.code == pure_code
        ),
        AShareIndicator.period == period,
        AShareIndicator.trade_date.in_(trade_dates)
    )
    indicator_result = await db.execute(indicator_query)
    indicators = indicator_result.scalars().all()

    indicator_map = {(i.trade_date): i for i in indicators}

    items = []
    for kline in klines:
        indicator = indicator_map.get(kline.trade_date)
        items.append(KlineIndicatorResponse(
            kline=KlineResponse.model_validate(kline),
            indicator=IndicatorResponse.model_validate(indicator) if indicator else None
        ))

    count_query = select(func.count()).select_from(
        select(AShareKline).where(
            AShareKline.code == code,
            AShareKline.period == period
        ).subquery()
    )
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return KlineListResponse(
        total=total,
        items=items,
        code=code,
        period=period
    )


async def _save_kline_data(db, kline_records, indicator_records):
    """保存K线数据和指标数据"""
    if not kline_records:
        return 0

    for kline in kline_records:
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
        await db.execute(on_conflict_stmt)

    for indicator in indicator_records:
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
        await db.execute(on_conflict_stmt)

    await db.commit()
    return len(kline_records)


async def _sync_single_stock_kline(db, code, period, full_sync=True):
    """同步单个股票的K线数据"""
    if not is_valid_stock_code(code):
        return 0

    ak_code = _convert_code(code)
    start_date = get_sync_start_date(full_sync, period)

    df = await asyncio.to_thread(load_kline_data_from_akshare, ak_code, period, start_date)
    if df is None:
        return 0

    kline_records, indicator_records = parse_kline_data(df, ak_code, period)
    return await _save_kline_data(db, kline_records, indicator_records)


async def _sync_single_stock_kline_with_db(code, period, full_sync):
    """带数据库连接的单个股票K线同步（用于并发执行）"""
    async with async_session_maker() as session:
        return await _sync_single_stock_kline(session, code, period, full_sync)


@router.post("/{code}/sync-all-indicators", summary="同步股票所有周期指标数据")
async def sync_stock_all_indicators(
    code: str,
    current_user = Depends(get_current_active_user)
):
    """同步股票所有周期（日线/周线/月线/年线）的K线和指标数据"""
    pure_code = extract_pure_code(code)
    
    tasks = [
        asyncio.create_task(_sync_single_stock_kline_with_db(pure_code, period, full_sync=True))
        for period in [1, 2, 3, 4]
    ]
    
    results = await asyncio.gather(*tasks)
    
    result_map = {f"period_{i+1}": results[i] for i in range(4)}
    
    for period, count in result_map.items():
        logger.info(f"同步 {pure_code} {period}, 写入 {count} 条")

    return {"code": pure_code, "results": result_map, "message": "所有周期数据同步完成"}


@router.post("/{code}/sync-recent-data", summary="同步股票最近数据")
async def sync_stock_recent_data(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """同步股票最近数据，按周期类型获取不同时间范围：
    - 日线: 最近30天
    - 周线: 最近60天(约8周)
    - 月线: 最近120天(约4个月)
    - 年线: 最近365天(约1年)
    """
    pure_code = extract_pure_code(code)

    tasks = [_sync_single_stock_kline(db, pure_code, period, full_sync=False) for period in [1, 2, 3, 4]]
    results = await asyncio.gather(*tasks)

    period_names = {1: "日线", 2: "周线", 3: "月线", 4: "年线"}
    total_count = sum(results)
    detail = {period_names[p]: results[i] for i, p in enumerate([1, 2, 3, 4])}

    return {"code": pure_code, "count": total_count, "detail": detail, "message": f"最近数据同步完成，共 {total_count} 条"}


@router.get("/{code}/financial-report", response_model=FinancialReportListResponse, summary="获取股票财务报表数据")
async def get_stock_financial_report(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> FinancialReportListResponse:
    """获取股票的季度财务报表数据"""
    pure_code = extract_pure_code(code)

    query = select(AShareFinancialReport).where(AShareFinancialReport.code == pure_code)\
        .order_by(AShareFinancialReport.report_period.desc())
    
    result = await db.execute(query)
    reports = result.scalars().all()

    count_query = select(func.count()).select_from(
        select(AShareFinancialReport).where(AShareFinancialReport.code == pure_code).subquery()
    )
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return FinancialReportListResponse(
        total=total,
        items=[FinancialReportResponse.model_validate(r) for r in reports],
        code=code
    )


async def _sync_single_stock_financial_report(code: str) -> int:
    """同步单个股票的财务报表数据"""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'jobs'))
    
    from jobs.financial_report_sync import sync_financial_report_for_stock
    return await sync_financial_report_for_stock(code)


@router.post("/{code}/sync-financial-report", summary="同步股票财务报表数据")
async def sync_stock_financial_report(
    code: str,
    current_user = Depends(get_current_active_user)
):
    """同步股票的财务报表数据，获取近一年的季度数据，如果获取到数据，删除之前的数据后再存储"""
    pure_code = extract_pure_code(code)
    
    result = await _sync_single_stock_financial_report(pure_code)
    
    logger.info(f"同步 {pure_code} 财务报表数据，写入 {result} 条")
    
    return {"code": pure_code, "count": result, "message": f"财务报表数据同步完成，共 {result} 条"}


@router.post("/{code}/sync-basic", summary="同步股票基础数据")
async def sync_stock_basic(
    code: str,
    current_user = Depends(get_current_active_user)
):
    """同步单只股票的基础数据（包括最新价、涨跌幅、股息率等）"""
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'jobs'))
    
    from jobs.a_share_basic_sync import _get_single_stock_data_sync, _get_single_stock_dividend_sync, _get_single_stock_pe_pb_sync, _infer_board_label, _num
    
    pure_code = extract_pure_code(code)
    
    try:
        stock_data = await asyncio.to_thread(_get_single_stock_data_sync, pure_code)
        if not stock_data:
            raise HTTPException(status_code=404, detail=f"未找到股票 {pure_code}")
        
        dividend_amount, _ = await asyncio.to_thread(_get_single_stock_dividend_sync, pure_code)
        pe_dynamic, pb = await asyncio.to_thread(_get_single_stock_pe_pb_sync, pure_code)
        
        latest_price = _num(stock_data.get("最新价")) or _num(stock_data.get("close"))
        
        dividend_yield = None
        if dividend_amount and latest_price and latest_price > 0:
            dividend_yield = round((dividend_amount / latest_price) * 100, 4)
        
        board_label = _infer_board_label(pure_code)
        
        async with async_session_maker() as session:
            insert_stmt = mysql_insert(AShareStockBasic).values(
                code=pure_code,
                name=stock_data.get("名称") or stock_data.get("name") or "未知",
                board_label=board_label,
                dividend_yield=dividend_yield,
                dividend_yield_as_of=None,
                latest_price=latest_price,
                change_pct=_num(stock_data.get("涨跌幅")),
                change_amount=_num(stock_data.get("涨跌额")),
                volume=_num(stock_data.get("成交量")),
                amount=_num(stock_data.get("成交额")),
                amplitude=_num(stock_data.get("振幅")),
                high=_num(stock_data.get("最高")),
                low=_num(stock_data.get("最低")),
                open_price=_num(stock_data.get("今开")),
                prev_close=_num(stock_data.get("昨收")),
                volume_ratio=_num(stock_data.get("量比")),
                turnover_rate=_num(stock_data.get("换手率")),
                pe_dynamic=pe_dynamic,
                pb=pb,
                total_market_cap=_num(stock_data.get("总市值")),
                circulating_market_cap=_num(stock_data.get("流通市值")),
                rise_speed=_num(stock_data.get("涨速")),
                change_5min=_num(stock_data.get("5分钟涨跌幅")),
                change_60d=_num(stock_data.get("60日涨跌幅")),
                change_ytd=_num(stock_data.get("年初至今涨跌幅")),
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
        
        logger.info(f"同步 {pure_code} 基础数据完成")
        
        return {
            "code": pure_code,
            "name": stock_data.get("名称") or stock_data.get("name") or "未知",
            "dividend_yield": dividend_yield,
            "latest_price": latest_price,
            "message": f"基础数据同步完成"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"同步 {pure_code} 基础数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")
