import time
import sqlite3

DB = "/data/data/com.termux/files/home/vasuki/data/vasuki.db"

while True:
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM file_inventory")
        count = cur.fetchone()[0]

        print(f"[VASUKI] Indexed files: {count}")

        conn.close()

    except Exception as e:
        print("ERROR:", e)

    time.sleep(60)
