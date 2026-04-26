import asyncio
from database import init_db, async_session_maker
from models import User
from auth import get_password_hash

async def create_default_admin():
    await init_db()

    async with async_session_maker() as session:
        from sqlalchemy import select
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

if __name__ == "__main__":
    asyncio.run(create_default_admin())
