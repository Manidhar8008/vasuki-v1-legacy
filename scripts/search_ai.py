import sqlite3
import sys

DB = "/data/data/com.termux/files/home/vasuki/data/vasuki.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

query = " ".join(sys.argv[1:])

if not query:
    print("Usage: python search_ai.py keyword")
    exit()

cur.execute("""
SELECT
    filename,
    path,
    size
FROM file_inventory
WHERE
    filename LIKE ?
    OR path LIKE ?
LIMIT 50
""", (f"%{query}%", f"%{query}%"))

rows = cur.fetchall()

print("\nRESULTS\n")

for r in rows:
    print(f"FILE : {r[0]}")
    print(f"PATH : {r[1]}")
    print(f"SIZE : {r[2]}")
    print("-"*50)

print(f"\nFound {len(rows)} files")

