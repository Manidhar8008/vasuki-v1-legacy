import os
import sqlite3
from pathlib import Path

DB = os.path.expanduser("~/vasuki/data/vasuki.db")

SCAN_DIRS = [
    os.path.expanduser("~/storage/shared/Download"),
    os.path.expanduser("~/storage/shared/Documents"),
    os.path.expanduser("~/storage/shared/DCIM"),
]

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS file_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE,
    filename TEXT,
    extension TEXT,
    size_bytes INTEGER,
    directory TEXT,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

new_files = 0
total_scanned = 0

for root_dir in SCAN_DIRS:

    if not os.path.exists(root_dir):
        print(f"Missing: {root_dir}")
        continue

    for root, dirs, files in os.walk(root_dir):

        for file in files:

            try:
                full_path = os.path.join(root, file)

                filename = os.path.basename(full_path)

                extension = Path(file).suffix.lower()

                size_bytes = os.path.getsize(full_path)

                cur.execute("""
                INSERT OR IGNORE INTO file_inventory
                (
                    path,
                    filename,
                    extension,
                    size_bytes,
                    directory
                )
                VALUES (?,?,?,?,?)
                """,
                (
                    full_path,
                    filename,
                    extension,
                    size_bytes,
                    root
                ))

                if cur.rowcount > 0:
                    new_files += 1

                total_scanned += 1

            except Exception as e:
                print("ERROR:", full_path, e)

conn.commit()

cur.execute("SELECT COUNT(*) FROM file_inventory")
total_files = cur.fetchone()[0]

print("=" * 50)
print("SCAN COMPLETE")
print("=" * 50)
print("Files scanned :", total_scanned)
print("New files     :", new_files)
print("Database rows :", total_files)

conn.close()
