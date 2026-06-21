import os
import sqlite3
from pathlib import Path

DB = "/data/data/com.termux/files/home/vasuki/data/vasuki.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS file_inventory(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE,
    filename TEXT,
    extension TEXT,
    size INTEGER
)
""")

ROOT = os.path.expanduser("~/storage/shared")

count = 0

for root, dirs, files in os.walk(ROOT):

    for file in files:

        try:
            path = os.path.join(root, file)

            cur.execute("""
            INSERT OR IGNORE INTO file_inventory
            (path,filename,extension,size)
            VALUES(?,?,?,?)
            """,(
                path,
                file,
                Path(file).suffix.lower(),
                os.path.getsize(path)
            ))

            count += 1

            if count % 100 == 0:
                conn.commit()
                print("Indexed:", count)

        except Exception:
            pass

conn.commit()

print("Finished:", count)

conn.close()
