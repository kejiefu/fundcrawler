"""
K线数据同步核心模块
供后端API和Jobs定时任务共同使用
支持多周期同步(日线/周线/月线/年线)
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional

import pandas as pd
import numpy as np

PERIOD_DAILY = 1
PERIOD_WEEKLY = 2
PERIOD_MONTHLY = 3
PERIOD_YEARLY = 4

PERIOD_MAP = {
    PERIOD_DAILY: "daily",
    PERIOD_WEEKLY: "weekly",
    PERIOD_MONTHLY: "monthly",
    PERIOD_YEARLY: "yearly"
}

THIRTY_DAYS = 30


def _num(v: Any, decimals: int = 4) -> float | None:
    """Convert value to float, None/NaN returns None, rounds to specified decimals"""
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
        return round(x, decimals)
    except (TypeError, ValueError):
        return None


def _convert_code(code: str) -> str:
    """Convert stock code to format required by AKShare"""
    code = str(code).strip()

    if code.lower().startswith('sh'):
        return f"sh{code[2:].zfill(6)}"
    elif code.lower().startswith('sz'):
        return f"sz{code[2:].zfill(6)}"
    elif code.lower().startswith('bj'):
        return f"bj{code[2:].zfill(6)}"
    elif code.startswith('6'):
        return f"sh{code.zfill(6)}"
    elif code.startswith('8') or code.startswith('4'):
        return f"bj{code.zfill(6)}"
    else:
        return f"sz{code.zfill(6)}"


def is_valid_stock_code(code: str) -> bool:
    """检查股票代码是否为有效的A股股票代码（过滤债券等）"""
    code = str(code).strip().lower()

    if code.startswith('sh'):
        pure_code = code[2:].zfill(6)
        return pure_code.startswith('6')

    elif code.startswith('sz'):
        pure_code = code[2:].zfill(6)
        return pure_code.startswith('0') or pure_code.startswith('3')

    elif code.startswith('bj'):
        pure_code = code[2:].zfill(6)
        return pure_code.startswith('8')

    elif len(code) == 6:
        return code.startswith('6') or code.startswith('0') or code.startswith('3') or code.startswith('8')

    return False


def get_sync_start_date(needs_full: bool, period: int = 1) -> str:
    """获取同步的开始日期，支持按周期类型设置不同的同步范围"""
    if needs_full:
        return "20000101"
    else:
        # 根据周期类型设置不同的同步天数
        # 日线: 最近30天, 周线: 最近60天(约8周), 月线: 最近120天(约4个月), 年线: 最近365天(约1年)
        days_map = {
            1: 30,   # 日线
            2: 60,   # 周线
            3: 120,  # 月线
            4: 365   # 年线
        }
        days = days_map.get(period, 30)
        start_date = datetime.now() - timedelta(days=days)
        return start_date.strftime("%Y%m%d")


def _calculate_kdj(data: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
    """计算KDJ指标 - 处理除以零的情况"""
    low_list = data['low'].rolling(window=n).min()
    high_list = data['high'].rolling(window=n).max()
    
    diff = high_list - low_list
    diff = diff.replace(0, np.nan)
    rsv = (data['close'] - low_list) / diff * 100

    k = rsv.ewm(alpha=1/m1, adjust=False).mean()
    d = k.ewm(alpha=1/m2, adjust=False).mean()
    j = 3 * k - 2 * d

    data['k_value'] = k
    data['d_value'] = d
    data['j_value'] = j
    return data


def _calculate_rsi(data: pd.DataFrame, periods: Tuple[int, int, int] = (6, 12, 24)) -> pd.DataFrame:
    """计算RSI指标 - 使用EMA平均，与东方财富/同花顺一致"""
    delta = data['close'].diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    for period in periods:
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        
        avg_loss = avg_loss.replace(0, np.nan)
        rs = avg_gain / avg_loss
        rs = rs.replace([np.inf, -np.inf], np.nan)
        rsi = 100 - (100 / (1 + rs))
        data[f'rsi_{period}'] = rsi

    return data


def load_kline_data_from_akshare(code: str, period: int, start_date: str = "20200101") -> pd.DataFrame | None:
    """从AKShare加载K线数据"""
    import akshare as ak

    try:
        pure_code = code[-6:]
        period_str = PERIOD_MAP.get(period, "daily")
        df = ak.stock_zh_a_hist(symbol=pure_code, period=period_str, start_date=start_date)

        if df is None or df.empty:
            return None

        return df
    except Exception:
        return None


def parse_kline_data(df: pd.DataFrame, code: str, period: int) -> Tuple[list, list]:
    """解析K线数据并计算指标，返回(kline_records, indicator_records)"""
    df = df.copy()

    df.columns = [col.strip() for col in df.columns]

    rename_map = {
        '日期': 'date',
        '开盘': 'open',
        '收盘': 'close',
        '最高': 'high',
        '最低': 'low',
        '成交量': 'volume',
        '成交额': 'amount'
    }
    df = df.rename(columns=rename_map)

    df['date'] = df['date'].astype(str).str.replace('-', '')

    df['open'] = df['open'].apply(_num)
    df['close'] = df['close'].apply(_num)
    df['high'] = df['high'].apply(_num)
    df['low'] = df['low'].apply(_num)
    df['volume'] = df['volume'].apply(_num)
    df['amount'] = df['amount'].apply(_num)

    df['prev_close'] = df['close'].shift(1)

    df['change_amount'] = df['close'] - df['prev_close']
    df['change_pct'] = (df['change_amount'] / df['prev_close']) * 100
    df['amplitude'] = ((df['high'] - df['low']) / df['prev_close']) * 100

    df = _calculate_kdj(df)
    df = _calculate_rsi(df)

    df = df.replace({np.nan: None, np.inf: None, -np.inf: None})

    kline_records = []
    indicator_records = []

    for _, row in df.iterrows():
        kline_record = {
            'code': code[-6:],
            'trade_date': row['date'],
            'period': period,
            'open_price': row['open'],
            'close_price': row['close'],
            'high_price': row['high'],
            'low_price': row['low'],
            'volume': row['volume'],
            'amount': row['amount'],
            'prev_close': _num(row['prev_close']),
            'change_pct': _num(row['change_pct']),
            'change_amount': _num(row['change_amount']),
            'amplitude': _num(row['amplitude'])
        }
        kline_records.append(kline_record)

        indicator_record = {
            'code': code[-6:],
            'trade_date': row['date'],
            'period': period,
            'k_value': _num(row.get('k_value')),
            'd_value': _num(row.get('d_value')),
            'j_value': _num(row.get('j_value')),
            'rsi_6': _num(row.get('rsi_6')),
            'rsi_12': _num(row.get('rsi_12')),
            'rsi_24': _num(row.get('rsi_24'))
        }
        indicator_records.append(indicator_record)

    return kline_records, indicator_records


def sync_kline_for_stock(code: str, period: int, full_sync: bool = True) -> Tuple[int, int]:
    """
    同步单个股票的K线数据
    返回: (kline_count, indicator_count)
    """
    if not is_valid_stock_code(code):
        return 0, 0

    ak_code = _convert_code(code)
    start_date = get_sync_start_date(full_sync)

    df = load_kline_data_from_akshare(ak_code, period, start_date)
    if df is None:
        return 0, 0

    kline_records, indicator_records = parse_kline_data(df, ak_code, period)

    return len(kline_records), len(indicator_records)
