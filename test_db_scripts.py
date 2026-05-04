import asyncio
import aiosqlite

DB_PATH = "spoiler_alert.db"

async def clear_tables():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM food_items;")
        rows = await cursor.fetchall()
        print(rows)

if __name__ == "__main__":
    asyncio.run(clear_tables())