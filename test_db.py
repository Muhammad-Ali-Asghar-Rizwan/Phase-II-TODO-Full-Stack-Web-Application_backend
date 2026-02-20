import asyncio
import asyncpg
import sys

async def test_connection():
    dsn = "postgresql://user:password@localhost:5432/todo_db"
    print(f"Testing connection to: {dsn}")
    try:
        conn = await asyncpg.connect(dsn)
        print("Success! Connected to database.")
        await conn.close()
        sys.exit(0)
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

asyncio.run(test_connection())
