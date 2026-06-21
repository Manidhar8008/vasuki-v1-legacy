import os
import time
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT = Path.home() / "storage" / "shared"
DB = Path.home() / "vasuki" / "data" / "vasuki.db"

os.makedirs(DB.parent, exist_ok=True)

conn = sqlite3.connect(DB, check_same_thread=False)
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

def enqueue(file_path):
    try:
        cur.execute("""
        INSERT OR IGNORE INTO processing_queue(path, status, updated_at)
        VALUES (?, 'pending', ?)
        """, (str(file_path), datetime.now().isoformat()))
    except Exception as e:
        print("ENQUEUE ERROR:", e)

def scan():
    for root, _, files in os.walk(ROOT):
        for f in files:
            yield os.path.join(root, f)

def loop():
    print("QUEUE DAEMON STARTED")

    while True:
        try:
            count = 0

            for file_path in scan():
                enqueue(file_path)
                count += 1

            conn.commit()
            print("SCAN DONE | files seen:", count)

        except Exception as e:
            print("SCAN LOOP ERROR:", e)

        time.sleep(20)

if __name__ == "__main__":
    loop()
