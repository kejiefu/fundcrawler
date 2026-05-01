import asyncio
import asyncmy

async def create_database():
    conn = None
    try:
        # Connect to MySQL server without specifying database
        conn = await asyncmy.connect(
            host='localhost',
            port=3306,
            user='root',
            password='999888777',
            charset='utf8mb4'
        )
        
        # Create database if it doesn't exist
        async with conn.cursor() as cursor:
            await cursor.execute(
                "CREATE DATABASE IF NOT EXISTS stock_fund_analysis CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            print("Database 'stock_fund_analysis' created successfully")
            
    finally:
        if conn:
            await conn.ensure_closed()

if __name__ == "__main__":
    asyncio.run(create_database())
