import os
import sqlite3
from pathlib import Path
from datetime import datetime

DB = "/data/data/com.termux/files/home/vasuki/data/vasuki.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE,
    filename TEXT,
    extension TEXT,
    size INTEGER,
    modified_time TEXT,
    category TEXT
)
""")

ROOTS = [
    "/storage/emulated/0/Download",
    "/storage/emulated/0/Documents",
    "/storage/emulated/0/Pictures",
    "/storage/emulated/0/DCIM",
    "/storage/emulated/0/ai_brain_feed"
]

for root_dir in ROOTS:

    for root, dirs, files in os.walk(root_dir):

        for file in files:

            try:

                full_path = os.path.join(root, file)

                size = os.path.getsize(full_path)

                ext = Path(file).suffix.lower()

                modified = datetime.fromtimestamp(
                    os.path.getmtime(full_path)
                ).isoformat()

                cur.execute("""
                INSERT OR IGNORE INTO files
                (
                    path,
                    filename,
                    extension,
                    size,
                    modified_time,
                    category
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    full_path,
                    file,
                    ext,
                    size,
                    modified,
                    "unclassified"
                ))

            except Exception:
                pass

conn.commit()
conn.close()

print("Inventory complete")
