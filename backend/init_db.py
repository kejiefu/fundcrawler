import asyncio
from sqlalchemy import select
from database import init_db, async_session_maker
from models import User, Menu
from auth import get_password_hash

# Default menu data
DEFAULT_MENUS = [
    {
        "name": "数据看板",
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
        "name": "股票基本信息",
        "path": "/stocks/basic",
        "icon": "LineChart",
        "parent_id": 3,
        "order": 1,
        "permission": "stock.basic.view"
    },
    {
        "name": "蓝筹股",
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
    """Create default admin user if not exists"""
    await init_db()

    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        existing_admin = result.scalar_one_or_none()

        if not existing_admin:
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
            print("Default admin user created: admin / admin123")
        else:
            print("Admin user already exists")

async def create_default_menus() -> None:
    """Create default menus if not exists"""
    async with async_session_maker() as session:
        result = await session.execute(select(Menu))
        existing_menus = result.scalars().all()
        
        if existing_menus:
            print("Menu data already exists, skipping creation")
            return
        
        # First create parent menus (parent_id is None)
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
        
        # Build name -> id mapping
        name_to_id = {}
        for menu_data in parent_menus:
            result = await session.execute(
                select(Menu).where(Menu.name == menu_data["name"])
            )
            created_menu = result.scalar_one()
            name_to_id[menu_data["name"]] = created_menu.id
        
        # Create child menus
        for menu_data in DEFAULT_MENUS:
            if menu_data.get("parent_id") is not None:
                parent_name = None
                if "Stock Info" in menu_data["name"] or "Bluechip" in menu_data["name"]:
                    parent_name = "Stock Management"
                elif "Menu Management" in menu_data["name"] or "Permission" in menu_data["name"]:
                    parent_name = "System Management"
                
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
        print("Default menus created")

async def init_data():
    """Initialize all default data"""
    await create_default_admin()
    await create_default_menus()

if __name__ == "__main__":
    asyncio.run(init_data())
