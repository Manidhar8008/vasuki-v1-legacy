
import sqlite3
from pathlib import Path

db_path = Path("../data/vasuki.db")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE,
    name TEXT,
    size INTEGER,
    modified REAL
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    category TEXT,
    content TEXT
)
""")

conn.commit()
conn.close()

print("Database created:", db_path)

