import sqlite3
from pathlib import Path

DB = Path.home() / "vasuki" / "data" / "vasuki.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("""
SELECT
    object_id,
    source_file,
    first_seen,
    last_seen,
    confidence
FROM provenance
""")

rows = cur.fetchall()

added = 0

for row in rows:

    object_id = row[0]
    source_file = row[1]
    first_seen = row[2]
    last_seen = row[3]
    confidence = row[4]

    cur.execute("""
    INSERT OR IGNORE INTO identity_objects(
        object_id,
        current_path,
        fingerprint,
        first_seen,
        last_seen,
        occurrence_count,
        confidence
    )
    VALUES(?,?,?,?,?,?,?)
    """, (
        object_id,
        source_file,
        object_id,
        first_seen,
        last_seen,
        1,
        confidence
    ))

    added += 1

conn.commit()

print()
print("IDENTITY OBJECTS CREATED:", added)
print()

conn.close()
