import sqlite3

# Connect to your database
conn = sqlite3.connect("database.db")   # Use EXACT same DB name as shown
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE items ADD COLUMN status TEXT DEFAULT 'pending'")
    cursor.execute("ALTER TABLE items ADD COLUMN risk_score REAL")
    cursor.execute("ALTER TABLE items ADD COLUMN risk_level TEXT")
    
    conn.commit()
    print("✅ Table updated successfully!")

except Exception as e:
    print("❌ Error:", e)

finally:
    conn.close()