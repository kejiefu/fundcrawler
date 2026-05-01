from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    """用户表 - 存储系统用户信息"""
    
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, comment="用户唯一标识")
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, index=True, nullable=False, comment="邮箱地址")
    hashed_password = Column(String(255), nullable=False, comment="加密后的密码")
    full_name = Column(String(100), comment="真实姓名")
    is_active = Column(Boolean, default=True, comment="账户是否激活")
    is_superuser = Column(Boolean, default=False, comment="是否为超级管理员")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

class Menu(Base):
    """菜单表 - 存储系统菜单信息"""
    
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True, comment="菜单唯一标识")
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

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="主键")
    code = Column(String(10), unique=True, index=True, nullable=False, comment="证券代码")
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
