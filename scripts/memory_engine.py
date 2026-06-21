import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path.home() / "vasuki/data/vasuki.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Create memory table (if not exists)
cur.execute("""
CREATE TABLE IF NOT EXISTS memory_events (
    id INTEGER PRIMARY KEY,
    file_path TEXT,
    event_type TEXT,
    title TEXT,
    importance INTEGER,
    year INTEGER,
    extracted_snippet TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

# Pull real extracted data
rows = cur.execute("""
SELECT file_path, content
FROM extracted_text
WHERE content IS NOT NULL
""").fetchall()

def classify(path, text):
    p = path.lower()

    if "cv" in p or "resume" in p:
        return "career_document"
    if "salary" in p or "pay" in p:
        return "financial_record"
    if "offer" in p:
        return "job_offer"
    if "statement" in p or "bank" in p:
        return "bank_record"
    if "course" in p:
        return "learning"
    return "general_document"

count = 0

for path, text in rows:
    try:
        text = text[:2000]
        event = classify(path, text)

        year = None
        for y in range(2010, 2027):
            if str(y) in text:
                year = y
                break

        title = path.split("/")[-1]

        cur.execute("""
        INSERT INTO memory_events(
            file_path,
            event_type,
            title,
            importance,
            year,
            extracted_snippet
        )
        VALUES(?,?,?,?,?,?)
        """, (
            path,
            event,
            title,
            1,
            year,
            text[:500]
        ))

        count += 1

    except Exception:
        continue

conn.commit()
conn.close()

print("MEMORY EVENTS CREATED:", count)
