from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import List, Optional
from database import get_db
from models import AShareStockBasic
from schemas import StockBasicResponse, StockListResponse
from auth import get_current_active_user

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

@router.get("/{code}", response_model=StockBasicResponse, summary="Get single stock info")
async def get_stock(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
) -> StockBasicResponse:
    """Get stock detailed info by code"""
    query = select(AShareStockBasic).where(AShareStockBasic.code == code)
    result = await db.execute(query)
    stock = result.scalar_one_or_none()

    if not stock:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Stock not found")

    return StockBasicResponse.model_validate(stock)
