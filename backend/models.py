from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    """用户表 - 存储系统用户信息"""
    
    __tablename__ = "users"
    __table_args__ = {'comment': '用户表 - 存储系统用户信息'}

    id = Column(Integer, primary_key=True, comment="用户唯一标识")
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, comment="邮箱地址")
    hashed_password = Column(String(255), nullable=False, comment="加密后的密码")
    full_name = Column(String(100), comment="真实姓名")
    is_active = Column(Boolean, default=True, comment="账户是否激活")
    is_superuser = Column(Boolean, default=False, comment="是否为超级管理员")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

class Menu(Base):
    """菜单表 - 存储系统菜单信息"""
    
    __tablename__ = "menus"
    __table_args__ = {'comment': '菜单表 - 存储系统菜单信息'}

    id = Column(Integer, primary_key=True, comment="菜单唯一标识")
    name = Column(String(50), nullable=False, comment="菜单名称")
    path = Column(String(100), comment="路由路径")
    icon = Column(String(50), comment="菜单图标")
    parent_id = Column(Integer, ForeignKey("menus.id"), nullable=True, comment="父菜单ID")
    order = Column(Integer, default=0, comment="排序序号")
    is_active = Column(Boolean, default=True, comment="是否启用")
    permission = Column(String(100), comment="权限标识")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    
    children = relationship("Menu", backref="parent", remote_side=[id])


class AShareStockBasic(Base):
    """A股基本信息表 - 存储沪深京A股实时行情数据"""

    __tablename__ = "a_share_stock_basic"
    __table_args__ = {'comment': 'A股基本信息表 - 存储沪深京A股实时行情数据'}

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    code = Column(String(10), unique=True, nullable=False, comment="证券代码（纯数字格式，不带市场前缀，如600519）")
    name = Column(String(64), nullable=False, comment="证券简称")
    board_label = Column(String(32), nullable=True, comment="板块/市场推断")
    latest_price = Column(Numeric(14, 4), nullable=True, comment="最新价")
    change_pct = Column(Numeric(12, 4), nullable=True, comment="涨跌幅%")
    change_amount = Column(Numeric(14, 4), nullable=True, comment="涨跌额")
    volume = Column(Numeric(20, 2), nullable=True, comment="成交量(手)")
    amount = Column(Numeric(22, 2), nullable=True, comment="成交额(元)")
    amplitude = Column(Numeric(12, 4), nullable=True, comment="振幅%")
    high = Column(Numeric(14, 4), nullable=True, comment="最高")
    low = Column(Numeric(14, 4), nullable=True, comment="最低")
    open_price = Column(Numeric(14, 4), nullable=True, comment="今开")
    prev_close = Column(Numeric(14, 4), nullable=True, comment="昨收")
    volume_ratio = Column(Numeric(14, 4), nullable=True, comment="量比")
    turnover_rate = Column(Numeric(12, 4), nullable=True, comment="换手率%")
    pe_dynamic = Column(Numeric(14, 4), nullable=True, comment="市盈率-动态")
    pb = Column(Numeric(14, 4), nullable=True, comment="市净率")
    total_market_cap = Column(Numeric(22, 2), nullable=True, comment="总市值(元)")
    circulating_market_cap = Column(Numeric(22, 2), nullable=True, comment="流通市值(元)")
    rise_speed = Column(Numeric(12, 4), nullable=True, comment="涨速")
    change_5min = Column(Numeric(12, 4), nullable=True, comment="5分钟涨跌%")
    change_60d = Column(Numeric(12, 4), nullable=True, comment="60日涨跌幅%")
    change_ytd = Column(Numeric(12, 4), nullable=True, comment="年初至今涨跌幅%")
    dividend_yield = Column(Numeric(12, 4), nullable=True, comment="股息率%")
    dividend_yield_as_of = Column(
        String(12),
        nullable=True,
        comment="股息率对应报告期YYYYMMDD",
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")


class AShareKline(Base):
    """A股K线数据表 - 存储日线、周线、月线、年线数据"""

    __tablename__ = "a_share_kline"
    __table_args__ = (
        UniqueConstraint("code", "trade_date", "period", name="uk_kline_code_date_period"),
        {'comment': 'A股K线数据表 - 存储日线、周线、月线、年线数据'},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    code = Column(String(10), nullable=False, comment="证券代码（纯数字格式，不带市场前缀，如600519）")
    trade_date = Column(String(8), nullable=False, comment="交易日期(YYYYMMDD)")
    period = Column(Integer, nullable=False, comment="周期类型(1=日线,2=周线,3=月线,4=年线)")
    open_price = Column(Numeric(14, 4), nullable=True, comment="开盘价")
    close_price = Column(Numeric(14, 4), nullable=True, comment="收盘价")
    high_price = Column(Numeric(14, 4), nullable=True, comment="最高价")
    low_price = Column(Numeric(14, 4), nullable=True, comment="最低价")
    volume = Column(Numeric(20, 2), nullable=True, comment="成交量(手)")
    amount = Column(Numeric(22, 2), nullable=True, comment="成交额(元)")
    prev_close = Column(Numeric(14, 4), nullable=True, comment="前收盘价")
    change_pct = Column(Numeric(12, 4), nullable=True, comment="涨跌幅%")
    change_amount = Column(Numeric(14, 4), nullable=True, comment="涨跌额")
    amplitude = Column(Numeric(12, 4), nullable=True, comment="振幅%")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")


class AShareIndicator(Base):
    """A股技术指标表 - 存储KDJ、RSI等技术指标"""

    __tablename__ = "a_share_indicator"
    __table_args__ = (
        UniqueConstraint("code", "trade_date", "period", name="uk_indicator_code_date_period"),
        {'comment': 'A股技术指标表 - 存储KDJ、RSI等技术指标'},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    code = Column(String(10), nullable=False, comment="证券代码（纯数字格式，不带市场前缀，如600519）")
    trade_date = Column(String(8), nullable=False, comment="交易日期(YYYYMMDD)")
    period = Column(Integer, nullable=False, comment="周期类型(1=日线,2=周线,3=月线,4=年线)")
    k_value = Column(Numeric(10, 4), nullable=True, comment="KDJ-K值")
    d_value = Column(Numeric(10, 4), nullable=True, comment="KDJ-D值")
    j_value = Column(Numeric(10, 4), nullable=True, comment="KDJ-J值")
    rsi_6 = Column(Numeric(10, 4), nullable=True, comment="RSI-6日")
    rsi_12 = Column(Numeric(10, 4), nullable=True, comment="RSI-12日")
    rsi_24 = Column(Numeric(10, 4), nullable=True, comment="RSI-24日")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")


class AShareFinancialReport(Base):
    """A股财务报表表 - 存储季度财务数据"""

    __tablename__ = "a_share_financial_report"
    __table_args__ = (
        UniqueConstraint("code", "report_period", name="uk_financial_code_period"),
        {'comment': 'A股财务报表表 - 存储季度财务数据'},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    code = Column(String(10), nullable=False, comment="证券代码（纯数字格式，不带市场前缀，如600519）")
    name = Column(String(64), nullable=True, comment="证券简称")
    report_period = Column(String(8), nullable=False, comment="报告期(YYYYMMDD)")
    report_type = Column(Integer, nullable=False, comment="报告类型(1=一季度,2=半年报,3=三季度,4=年报)")
    eps = Column(Numeric(10, 4), nullable=True, comment="每股收益(元)")
    eps_yoy = Column(Numeric(10, 4), nullable=True, comment="每股收益同比增长率(%)")
    net_profit = Column(Numeric(20, 4), nullable=True, comment="净利润(元)")
    net_profit_yoy = Column(Numeric(10, 4), nullable=True, comment="净利润同比增长率(%)")
    net_profit_deducted = Column(Numeric(20, 4), nullable=True, comment="扣非净利润(元)")
    net_profit_deducted_yoy = Column(Numeric(10, 4), nullable=True, comment="扣非净利润同比增长率(%)")
    revenue = Column(Numeric(22, 4), nullable=True, comment="营业收入(元)")
    revenue_yoy = Column(Numeric(10, 4), nullable=True, comment="营业收入同比增长率(%)")
    roe = Column(Numeric(10, 4), nullable=True, comment="净资产收益率(%)")
    roa = Column(Numeric(10, 4), nullable=True, comment="总资产收益率(%)")
    gross_margin = Column(Numeric(10, 4), nullable=True, comment="毛利率(%)")
    operating_margin = Column(Numeric(10, 4), nullable=True, comment="营业利润率(%)")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
