import os
import sqlite3
from pathlib import Path

db = sqlite3.connect("vasuki.db")
cur = db.cursor()

for root, dirs, files in os.walk("/storage/emulated/0/Download"):

    for f in files:

        try:
            full_path = os.path.join(root, f)

            size = os.path.getsize(full_path)

            ext = Path(f).suffix.lower()

            cur.execute("""
            INSERT INTO files
            (
                path,
                filename,
                extension,
                size
            )
            VALUES (?, ?, ?, ?)
            """, (
                full_path,
                f,
                ext,
                size
            ))

        except Exception as e:
            print(e)

db.commit()
db.close()

print("Inventory Complete")
