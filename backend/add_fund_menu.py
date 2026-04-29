import asyncio
from sqlalchemy import select
from database import async_session_maker
from models import Menu

async def add_fund_menu():
    """添加基金菜单及其子菜单"""
    async with async_session_maker() as session:
        result = await session.execute(select(Menu).where(Menu.name == "基金"))
        fund_menu = result.scalar_one_or_none()

        if not fund_menu:
            result = await session.execute(select(Menu).order_by(Menu.order.desc()))
            max_order = result.scalars().first()
            new_order = (max_order.order + 1) if max_order else 1

            fund_menu = Menu(
                name="基金",
                path="/funds",
                icon="TrendingUp",
                parent_id=None,
                order=new_order,
                is_active=True,
                permission="funds.view"
            )
            session.add(fund_menu)
            await session.commit()
            await session.refresh(fund_menu)
            print(f"基金菜单已创建，ID: {fund_menu.id}, 排序: {new_order}")
        else:
            print(f"基金菜单已存在，ID: {fund_menu.id}")

        result = await session.execute(select(Menu).where(Menu.name == "股票基金"))
        stock_fund = result.scalar_one_or_none()

        if not stock_fund:
            result = await session.execute(select(Menu).where(Menu.name == "基金"))
            fund = result.scalar_one_or_none()

            result = await session.execute(select(Menu).where(Menu.parent_id == fund.id).order_by(Menu.order.desc()))
            max_order = result.scalars().first()
            new_order = (max_order.order + 1) if max_order else 1

            stock_fund = Menu(
                name="股票基金",
                path="/funds/stocks",
                icon="LineChart",
                parent_id=fund.id,
                order=new_order,
                is_active=True,
                permission="funds.stocks.view"
            )
            session.add(stock_fund)
            await session.commit()
            print(f"股票基金子菜单已创建，排序: {new_order}")
        else:
            print("股票基金子菜单已存在")

        result = await session.execute(select(Menu).where(Menu.name == "债券基金"))
        bond_fund = result.scalar_one_or_none()

        if not bond_fund:
            result = await session.execute(select(Menu).where(Menu.name == "基金"))
            fund = result.scalar_one_or_none()

            result = await session.execute(select(Menu).where(Menu.parent_id == fund.id).order_by(Menu.order.desc()))
            max_order = result.scalars().first()
            new_order = (max_order.order + 1) if max_order else 1

            bond_fund = Menu(
                name="债券基金",
                path="/funds/bonds",
                icon="BarChart",
                parent_id=fund.id,
                order=new_order,
                is_active=True,
                permission="funds.bonds.view"
            )
            session.add(bond_fund)
            await session.commit()
            print(f"债券基金子菜单已创建，排序: {new_order}")
        else:
            print("债券基金子菜单已存在")

if __name__ == "__main__":
    asyncio.run(add_fund_menu())
