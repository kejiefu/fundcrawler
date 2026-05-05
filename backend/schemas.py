from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class MenuBase(BaseModel):
    name: str
    path: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    order: int = 0
    is_active: bool = True
    permission: Optional[str] = None

class MenuCreate(MenuBase):
    pass

class MenuUpdate(MenuBase):
    name: Optional[str] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None

class MenuResponse(MenuBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    children: List['MenuResponse'] = []

    model_config = ConfigDict(from_attributes=True)

MenuResponse.model_rebuild()

class StockBasicResponse(BaseModel):
    id: int
    code: str
    name: str
    board_label: Optional[str] = None
    latest_price: Optional[float] = None
    change_pct: Optional[float] = None
    change_amount: Optional[float] = None
    volume: Optional[float] = None
    amount: Optional[float] = None
    amplitude: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open_price: Optional[float] = None
    prev_close: Optional[float] = None
    volume_ratio: Optional[float] = None
    turnover_rate: Optional[float] = None
    pe_dynamic: Optional[float] = None
    pb: Optional[float] = None
    total_market_cap: Optional[float] = None
    circulating_market_cap: Optional[float] = None
    rise_speed: Optional[float] = None
    change_5min: Optional[float] = None
    change_60d: Optional[float] = None
    change_ytd: Optional[float] = None
    dividend_yield: Optional[float] = None
    dividend_yield_as_of: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class StockListResponse(BaseModel):
    total: int
    items: List[StockBasicResponse]
    page: int
    page_size: int


class KlineResponse(BaseModel):
    id: int
    code: str
    trade_date: str
    period: int
    open_price: Optional[float] = None
    close_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    volume: Optional[float] = None
    amount: Optional[float] = None
    prev_close: Optional[float] = None
    change_pct: Optional[float] = None
    change_amount: Optional[float] = None
    amplitude: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class IndicatorResponse(BaseModel):
    id: int
    code: str
    trade_date: str
    period: int
    k_value: Optional[float] = None
    d_value: Optional[float] = None
    j_value: Optional[float] = None
    rsi_6: Optional[float] = None
    rsi_12: Optional[float] = None
    rsi_24: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class KlineIndicatorResponse(BaseModel):
    kline: KlineResponse
    indicator: Optional[IndicatorResponse] = None


class KlineListResponse(BaseModel):
    total: int
    items: List[KlineIndicatorResponse]
    code: str
    period: int


class FinancialReportResponse(BaseModel):
    id: int
    code: str
    name: Optional[str] = None
    report_period: str
    report_type: int
    eps: Optional[float] = None
    eps_yoy: Optional[float] = None
    net_profit: Optional[float] = None
    net_profit_yoy: Optional[float] = None
    net_profit_deducted: Optional[float] = None
    net_profit_deducted_yoy: Optional[float] = None
    revenue: Optional[float] = None
    revenue_yoy: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class FinancialReportListResponse(BaseModel):
    total: int
    items: List[FinancialReportResponse]
    code: str
