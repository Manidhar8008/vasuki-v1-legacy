import sqlite3
from pathlib import Path

DB = Path.home() / "vasuki/data/vasuki.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS memories(
    id INTEGER PRIMARY KEY,
    source_file TEXT,
    memory_type TEXT,
    summary TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

rows = cur.execute("""
SELECT file_path,content
FROM extracted_text
""").fetchall()

added = 0

for path,content in rows:

    text = (content or "").strip()

    if len(text) < 100:
        continue

    summary = text[:500]

    cur.execute("""
    INSERT INTO memories(
        source_file,
        memory_type,
        summary
    )
    VALUES(?,?,?)
    """,(
        path,
        "document",
        summary
    ))

    added += 1

conn.commit()

print("Memories created:",added)

conn.close()
