import asyncio
from sqlalchemy import select
from database import async_session_maker
from models import Menu

async def add_bluechip_menu():
    """添加蓝筹股票子菜单（股息率>3.5%）"""
    async with async_session_maker() as session:
        result = await session.execute(select(Menu).where(Menu.name == "股票"))
        stock_menu = result.scalar_one_or_none()

        if not stock_menu:
            print("股票菜单不存在，先创建股票菜单")
            result = await session.execute(select(Menu).order_by(Menu.order.desc()))
            max_order = result.scalars().first()
            new_order = (max_order.order + 1) if max_order else 1

            stock_menu = Menu(
                name="股票",
                path="/stocks",
                icon="TrendingUp",
                parent_id=None,
                order=new_order,
                is_active=True,
                permission="stocks.view"
            )
            session.add(stock_menu)
            await session.commit()
            await session.refresh(stock_menu)
            print(f"股票菜单已创建，ID: {stock_menu.id}, 排序: {new_order}")

        result = await session.execute(select(Menu).where(Menu.name == "蓝筹股票"))
        bluechip_menu = result.scalar_one_or_none()

        if not bluechip_menu:
            result = await session.execute(select(Menu).where(Menu.parent_id == stock_menu.id).order_by(Menu.order.desc()))
            max_order = result.scalars().first()
            new_order = (max_order.order + 1) if max_order else 1

            bluechip_menu = Menu(
                name="蓝筹股票",
                path="/stocks/bluechip",
                icon="BarChart",
                parent_id=stock_menu.id,
                order=new_order,
                is_active=True,
                permission="stocks.bluechip.view"
            )
            session.add(bluechip_menu)
            await session.commit()
            print(f"蓝筹股票子菜单已创建，排序: {new_order}")
        else:
            print("蓝筹股票子菜单已存在")

if __name__ == "__main__":
    asyncio.run(add_bluechip_menu())