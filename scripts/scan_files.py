
import os
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime

print("VASUKI COLLECTOR AGENT STARTING...")

ROOT = "/storage/emulated/0"

DB_PATH = "../data/vasuki.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    path TEXT UNIQUE,
    extension TEXT,
    size_mb REAL,
    modified_date TEXT,
    file_hash TEXT
)
""")

conn.commit()

count = 0
errors = 0


def get_hash(filepath):
    try:
        with open(filepath, "rb") as f:
            return hashlib.md5(f.read(1024 * 1024)).hexdigest()
    except:
        return None


for root, dirs, files in os.walk(ROOT):

    for file in files:

        try:

            full_path = os.path.join(root, file)

            size_mb = round(
                os.path.getsize(full_path) / (1024 * 1024),
                2
            )

            modified = datetime.fromtimestamp(
                os.path.getmtime(full_path)
            ).strftime("%Y-%m-%d %H:%M:%S")

            extension = Path(file).suffix.lower()

            file_hash = get_hash(full_path)

            cursor.execute("""
            INSERT OR IGNORE INTO files
            (
                name,
                path,
                extension,
                size_mb,
                modified_date,
                file_hash
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                file,
                full_path,
                extension,
                size_mb,
                modified,
                file_hash
            ))

            count += 1

            if count % 500 == 0:
                print(f"Collected {count} files...")

        except Exception:
            errors += 1

conn.commit()

cursor.execute("SELECT COUNT(*) FROM files")
total_files = cursor.fetchone()[0]

cursor.execute("""
SELECT extension, COUNT(*)
FROM files
GROUP BY extension
ORDER BY COUNT(*) DESC
LIMIT 20
""")

top_types = cursor.fetchall()

print("\n===================")
print("VASUKI REPORT")
print("===================")

print(f"Files Collected: {total_files}")
print(f"Errors: {errors}")

print("\nTOP FILE TYPES")

for ext, qty in top_types:
    print(ext, qty)

conn.close()

print("\nMEMORY

