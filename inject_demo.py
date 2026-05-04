import asyncio
import aiosqlite

DB_PATH = "spoiler_alert.db"

async def inject():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM predictions;")
        
        query = """
        INSERT INTO predictions (item_id, predicted_at, predicted_spoil_by, confidence, method) VALUES
        ('demo-item', '2026-05-01T10:00:00', '2026-05-03T10:00:00', 0.90, 'rule_based'),
        ('demo-item', '2026-05-02T10:00:00', '2026-05-03T08:00:00', 0.85, 'rule_based'),
        ('demo-item', '2026-05-03T08:00:00', '2026-05-03T14:00:00', 0.80, 'curve_fit'),
        ('demo-item', '2026-05-03T12:00:00', '2026-05-03T15:00:00', 0.78, 'curve_fit'),
        ('demo-item', '2026-05-04T06:00:00', '2026-05-04T12:00:00', 0.75, 'regression'),
        ('demo-item', '2026-05-04T10:00:00', '2026-05-04T14:00:00', 0.70, 'regression'),
        ('demo-item', '2026-05-05T09:00:00', '2026-05-05T10:00:00', 0.65, 'regression');
        """
        await db.execute(query)
        await db.commit()
        print("Demo data successfully injected.")

if __name__ == "__main__":
    asyncio.run(inject())
