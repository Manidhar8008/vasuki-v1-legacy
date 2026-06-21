import os
import time
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT = Path.home() / "storage" / "shared"
DB = Path.home() / "vasuki" / "data" / "vasuki.db"

conn = sqlite3.connect(DB, check_same_thread=False, timeout=30)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS processing_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE,
    status TEXT DEFAULT 'pending',
    created_at TEXT,
    updated_at TEXT
)
""")

conn.commit()

def scan():
    for root, _, files in os.walk(ROOT):
        for f in files:
            yield os.path.join(root, f)

def loop():
    print("WRITER STARTED")

    while True:
        try:
            count = 0

            for file_path in scan():
                try:
                    cur.execute("""
                    INSERT OR IGNORE INTO processing_queue(path, status, created_at, updated_at)
                    VALUES (?, 'pending', ?, ?)
                    """, (
                        file_path,
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    ))
                    count += 1

                except Exception:
                    pass

            conn.commit()
            print("SCAN DONE:", count)

        except Exception as e:
            print("WRITER ERROR:", e)

        time.sleep(30)

if __name__ == "__main__":
    loop()
