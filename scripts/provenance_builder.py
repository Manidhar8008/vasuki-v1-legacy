import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime

DB = Path.home() / "vasuki" / "data" / "vasuki.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

DEVICE_ID = "termux_primary"

cur.execute("DELETE FROM provenance")

try:
    cur.execute("""
    SELECT
        path
    FROM file_inventory
    """)
except:
    cur.execute("""
    SELECT
        file_path
    FROM extracted_text
    """)

rows = cur.fetchall()

added = 0

for row in rows:

    path = row[0]

    if not path:
        continue

    object_id = hashlib.sha256(
        path.encode("utf-8")
    ).hexdigest()

    now = datetime.utcnow().isoformat()

    cur.execute("""
    INSERT INTO provenance(
        object_id,
        source_file,
        device_id,
        first_seen,
        last_seen,
        confidence
    )
    VALUES(?,?,?,?,?,?)
    """, (
        object_id,
        path,
        DEVICE_ID,
        now,
        now,
        1.0
    ))

    added += 1

conn.commit()

print()
print("PROVENANCE RECORDS:", added)
print()

conn.close()
