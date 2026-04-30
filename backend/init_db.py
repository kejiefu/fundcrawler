import asyncio
from sqlalchemy import select
from database import init_db, async_session_maker
from models import User, Menu
from auth import get_password_hash

# 默认菜单数据
DEFAULT_MENUS = [
    {
        "name": "仪表盘",
        "path": "/dashboard",
        "icon": "LayoutDashboard",
        "order": 1,
        "permission": "dashboard.view"
    },
    {
        "name": "用户管理",
        "path": "/users",
        "icon": "Users",
        "order": 2,
        "permission": "users.view"
    },
    {
        "name": "股票管理",
        "path": None,
        "icon": "TrendingUp",
        "order": 3,
        "permission": "stock.view"
    },
    {
        "name": "股票信息",
        "path": "/stocks/basic",
        "icon": "LineChart",
        "parent_id": 3,
        "order": 1,
        "permission": "stock.basic.view"
    },
    {
        "name": "蓝筹股票",
        "path": "/stocks/bluechip",
        "icon": "BarChart",
        "parent_id": 3,
        "order": 2,
        "permission": "stock.bluechip.view"
    },
    {
        "name": "系统管理",
        "path": None,
        "icon": "Settings",
        "order": 4,
        "permission": "system.view"
    },
    {
        "name": "菜单管理",
        "path": "/menus",
        "icon": "Menu",
        "parent_id": 6,
        "order": 1,
        "permission": "menus.view"
    },
    {
        "name": "权限管理",
        "path": "/permissions",
        "icon": "Shield",
        "parent_id": 6,
        "order": 2,
        "permission": "permissions.view"
    }
]

async def create_default_admin() -> None:
    """创建默认管理员用户（如果不存在）"""
    # 初始化数据库表结构
    await init_db()

    async with async_session_maker() as session:
        # 检查管理员是否已存在
        result = await session.execute(select(User).where(User.username == "admin"))
        existing_admin = result.scalar_one_or_none()

        if not existing_admin:
            # 创建默认管理员
            admin_user = User(
                username="admin",
                email="admin@example.com",
                full_name="System Administrator",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_superuser=True
            )
            session.add(admin_user)
            await session.commit()
            print("默认管理员用户已创建: admin / admin123")
        else:
            print("管理员用户已存在")

async def create_default_menus() -> None:
    """创建默认菜单（如果不存在）"""
    async with async_session_maker() as session:
        result = await session.execute(select(Menu))
        existing_menus = result.scalars().all()
        
        if existing_menus:
            print("菜单数据已存在，跳过创建")
            return
        
        # 先创建所有父菜单（parent_id 为 None 的）
        parent_menus = []
        for menu_data in DEFAULT_MENUS:
            if menu_data.get("parent_id") is None:
                menu = Menu(
                    name=menu_data["name"],
                    path=menu_data.get("path"),
                    icon=menu_data["icon"],
                    parent_id=None,
                    order=menu_data["order"],
                    is_active=True,
                    permission=menu_data["permission"]
                )
                session.add(menu)
                parent_menus.append(menu_data)
        
        await session.flush()
        
        # 构建 name -> id 的映射
        name_to_id = {}
        for menu_data in parent_menus:
            result = await session.execute(
                select(Menu).where(Menu.name == menu_data["name"])
            )
            created_menu = result.scalar_one()
            name_to_id[menu_data["name"]] = created_menu.id
        
        # 再创建子菜单
        for menu_data in DEFAULT_MENUS:
            if menu_data.get("parent_id") is not None:
                parent_name = None
                for pm in parent_menus:
                    if pm.get("_order") == menu_data.get("parent_id"):
                        pass
        
        # 使用 name 映射找到 parent_id
        for menu_data in DEFAULT_MENUS:
            if menu_data.get("parent_id") is not None:
                parent_name = None
                if "股票信息" in menu_data["name"] or "蓝筹" in menu_data["name"]:
                    parent_name = "股票管理"
                elif "菜单管理" in menu_data["name"] or "权限管理" in menu_data["name"]:
                    parent_name = "系统管理"
                
                parent_id = name_to_id.get(parent_name)
                menu = Menu(
                    name=menu_data["name"],
                    path=menu_data.get("path"),
                    icon=menu_data["icon"],
                    parent_id=parent_id,
                    order=menu_data["order"],
                    is_active=True,
                    permission=menu_data["permission"]
                )
                session.add(menu)
        
        await session.commit()
        print("默认菜单已创建")

async def init_data():
    """初始化所有默认数据"""
    await create_default_admin()
    await create_default_menus()

if __name__ == "__main__":
    asyncio.run(init_data())
