import time
import sqlite3
from datetime import datetime

DB = "/data/data/com.termux/files/home/vasuki/data/vasuki.db"

conn = sqlite3.connect(DB, timeout=30)
cur = conn.cursor()

def fetch_batch():
    cur.execute("""
    SELECT id, path FROM processing_queue
    WHERE status='pending'
    LIMIT 10
    """)
    return cur.fetchall()

def mark(id, status):
    cur.execute("""
    UPDATE processing_queue
    SET status=?, updated_at=?
    WHERE id=?
    """, (status, datetime.now().isoformat(), id))

def loop():
    print("PROCESSOR STARTED")

    while True:
        try:
            rows = fetch_batch()

            if not rows:
                time.sleep(2)
                continue

            for id, path in rows:
                try:
                    mark(id, "processing")

                    print("PROCESS:", path)

                    mark(id, "done")
                    conn.commit()

                except Exception as e:
                    print("FILE ERROR:", e)
                    mark(id, "error")

        except Exception as e:
            print("LOOP ERROR:", e)

        time.sleep(1)

if __name__ == "__main__":
    loop()
