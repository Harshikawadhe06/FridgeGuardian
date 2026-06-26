import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

try:
    cursor.execute(
        "ALTER TABLE items ADD COLUMN completed_date TEXT"
    )

    conn.commit()
    print("✅ completed_date column added")

except Exception as e:
    print("❌ Error:", e)

finally:
    conn.close()