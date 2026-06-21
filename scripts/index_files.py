import sqlite3
from pathlib import Path

DB = Path.home() / "vasuki/data/vasuki.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS file_inventory(
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE,
    filename TEXT,
    extension TEXT,
    size INTEGER
)
""")

root = Path.home() / "storage/shared/Download"

count = 0

for f in root.rglob("*"):
    if f.is_file():
        try:
            cur.execute("""
            INSERT OR IGNORE INTO file_inventory
            (path, filename, extension, size)
            VALUES (?,?,?,?)
            """, (
                str(f),
                f.name,
                f.suffix.lower(),
                f.stat().st_size
            ))
            count += 1
        except:
            pass

conn.commit()
conn.close()

print("Indexed:", count)

