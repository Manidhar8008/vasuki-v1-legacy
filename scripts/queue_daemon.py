import os
import time
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT = Path.home() / "storage" / "shared"
DB = Path.home() / "vasuki" / "data" / "vasuki.db"

os.makedirs(DB.parent, exist_ok=True)

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS processing_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE,
    status TEXT DEFAULT 'pending',
    updated_at TEXT
)
""")

conn.commit()

def enqueue_file(file_path):
    try:
        cur.execute("""
        INSERT OR IGNORE INTO processing_queue(path, status, updated_at)
        VALUES (?, 'pending', ?)
        """, (str(file_path), datetime.now().isoformat()))
    except:
        pass

def scan_loop():
    print("SCAN DAEMON STARTED")

    while True:
        try:
            for root, _, files in os.walk(ROOT):
                for f in files:
                    full_path = os.path.join(root, f)
                    enqueue_file(full_path)

            conn.commit()
            print("SCAN ROUND COMPLETE")

        except Exception as e:
            print("SCAN ERROR:", e)

        time.sleep(30)

if __name__ == "__main__":
    scan_loop()
