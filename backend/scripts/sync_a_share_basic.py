#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
手动同步沪深京 A 股基本信息到表 a_share_stock_basic。

在 backend 目录执行:
    python scripts/sync_a_share_basic.py
"""

from __future__ import annotations

import asyncio
import os
import sys


def _backend_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> None:
    root = _backend_root()
    os.chdir(root)
    if root not in sys.path:
        sys.path.insert(0, root)

    async def _go() -> None:
        from database import init_db
        from jobs.a_share_basic_sync import sync_a_share_stock_basic_once

        await init_db()
        n = await sync_a_share_stock_basic_once()
        print(f"同步完成，条数: {n}")

    asyncio.run(_go())


if __name__ == "__main__":
    main()
