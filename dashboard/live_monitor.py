import sqlite3
import time
import os

DB = "/data/data/com.termux/files/home/vasuki/data/vasuki.db"

while True:
    os.system("clear")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    files = cur.execute(
        "SELECT COUNT(*) FROM files"
    ).fetchone()[0]

    memories = cur.execute(
        "SELECT COUNT(*) FROM memories"
    ).fetchone()[0]

    print("=" * 40)
    print("VASUKI LIVE STATUS")
    print("=" * 40)

    print("Files Indexed :", files)
    print("Memories      :", memories)

    conn.close()

    time.sleep(2)
