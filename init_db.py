import asyncio
import aiosqlite
from app.config import settings
from datetime import datetime

async def main():
    """
    Creates all tables in the SQLite database if they do not exist.
    """
    async with aiosqlite.connect(settings.DATABASE_URL) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        
        # 1. devices table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                device_id TEXT PRIMARY KEY,
                user_id TEXT,
                fcm_token TEXT,
                registered_at DATETIME
            )
        """)
        
        # 2. food_items table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS food_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT,
                label TEXT,
                food_category TEXT CHECK(food_category IN ('raw_meat', 'dairy', 'leafy', 'cooked')),
                placed_at DATETIME,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (device_id) REFERENCES devices (device_id)
            )
        """)
        
        # 3. color_readings table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS color_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                sticker_type TEXT,
                timestamp DATETIME,
                R REAL,
                G REAL,
                B REAL,
                H REAL,
                S REAL,
                V REAL,
                L_star REAL,
                a_star REAL,
                b_star REAL,
                spoilage_score REAL,
                FOREIGN KEY (item_id) REFERENCES food_items (item_id)
            )
        """)
        
        # 4. predictions table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                predicted_at DATETIME,
                predicted_spoil_by DATETIME,
                confidence REAL,
                method TEXT,
                FOREIGN KEY (item_id) REFERENCES food_items (item_id)
            )
        """)
        
        # 5. feedback table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                submitted_at DATETIME,
                actual_spoil_at DATETIME,
                predicted_spoil_at DATETIME,
                error_hours REAL,
                FOREIGN KEY (item_id) REFERENCES food_items (item_id)
            )
        """)
        
        await db.commit()
        print("Database tables created successfully.")

async def run_sanity_check():
    """
    Inserts a dummy device and reads it back to verify the database connection.
    """
    print("Running sanity check...")
    async with aiosqlite.connect(settings.DATABASE_URL) as db:
        test_device = {
            "device_id": "TEST_DEV_001",
            "user_id": "USER_456",
            "fcm_token": "TOKEN_XYZ",
            "registered_at": datetime.now().isoformat()
        }
        
        # Insert
        await db.execute(
            "INSERT OR REPLACE INTO devices (device_id, user_id, fcm_token, registered_at) VALUES (?, ?, ?, ?)",
            (test_device["device_id"], test_device["user_id"], test_device["fcm_token"], test_device["registered_at"])
        )
        await db.commit()
        
        # Read back
        async with db.execute("SELECT * FROM devices WHERE device_id = ?", (test_device["device_id"],)) as cursor:
            row = await cursor.fetchone()
            print(f"Sanity Check Result: {row}")

if __name__ == "__main__":
    # Create tables
    asyncio.run(main())
    # Perform sanity check
    asyncio.run(run_sanity_check())
