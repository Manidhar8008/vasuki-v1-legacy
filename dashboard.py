import sqlite3
import subprocess
import time
import os

DB = os.path.expanduser("~/vasuki/data/vasuki.db")

while True:
    os.system("clear")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM files")
    files = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM memories")
    memories = cur.fetchone()[0]

    conn.close()

    ram = subprocess.getoutput("free -h | grep Mem")
    disk = subprocess.getoutput("df -h /data | tail -1")

    print("="*40)
    print("VASUKI DASHBOARD")
    print("="*40)

    print(f"Files: {files}")
    print(f"Memories: {memories}")
    print()
    print(ram)
    print(disk)

    time.sleep(2)
