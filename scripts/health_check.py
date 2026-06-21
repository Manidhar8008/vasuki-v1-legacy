import sqlite3
import os

DB = os.path.expanduser("~/vasuki/data/vasuki.db")

print("=" * 50)
print("VASUKI HEALTH CHECK")
print("=" * 50)

if not os.path.exists(DB):
    print("❌ Database not found")
    exit()

print("✅ Database exists")

conn = sqlite3.connect(DB)
cur = conn.cursor()

try:
    cur.execute("SELECT COUNT(*) FROM file_inventory")
    count = cur.fetchone()[0]
    print(f"✅ Files indexed: {count}")
except Exception as e:
    print("❌ file_inventory error:", e)

tables = cur.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
""").fetchall()

print("\nTables:")

for t in tables:
    print(" -", t[0])

conn.close()

print("\nHealth check complete.")
