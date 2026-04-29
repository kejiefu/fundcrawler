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
        "name": "系统管理",
        "path": None,
        "icon": "Settings",
        "order": 3,
        "permission": "system.view"
    },
    {
        "name": "菜单管理",
        "path": "/menus",
        "icon": "Menu",
        "parent_id": 3,
        "order": 1,
        "permission": "menus.view"
    },
    {
        "name": "权限管理",
        "path": "/permissions",
        "icon": "Shield",
        "parent_id": 3,
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
        # 检查是否已有菜单
        result = await session.execute(select(Menu))
        existing_menus = result.scalars().all()
        
        if existing_menus:
            print("菜单数据已存在，跳过创建")
            return
        
        # 创建默认菜单
        created_menus = {}
        for menu_data in DEFAULT_MENUS:
            menu = Menu(
                name=menu_data["name"],
                path=menu_data["path"],
                icon=menu_data["icon"],
                parent_id=menu_data.get("parent_id"),
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
