#!/usr/bin/env python3
from pathlib import Path
import sqlite3

DB = Path.home() / "vasuki" / "vasuki_v2" / "data" / "vasuki_personal_memory.db"

def short(value, n=350):
    value = str(value)
    return value if len(value) <= n else value[:n] + "..."

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
cur = con.cursor()

print("=" * 80)
print("VASUKI PERSONAL SEARCH CONTENT PROBE v1")
print("=" * 80)

for table in ["personal_documents", "personal_chunks", "personal_search"]:
    print(f"\nTABLE: {table}")
    print("-" * 80)

    cols = [r["name"] for r in cur.execute(f'PRAGMA table_info("{table}")')]
    print("COLUMNS:", ", ".join(cols))

    rows = cur.execute(f'SELECT rowid, * FROM "{table}" LIMIT 3').fetchall()
    for index, row in enumerate(rows, 1):
        print(f"\nROW {index}:")
        for key, value in dict(row).items():
            print(f"  {key}: {short(value)}")

print("\n" + "=" * 80)
print("FTS TOKEN TESTS")
print("=" * 80)

tests = ["vasuki", "memory", "data", "workflow", "normalization", "phone", "project"]

for term in tests:
    try:
        count = cur.execute(
            'SELECT COUNT(*) AS n FROM "personal_search" WHERE "personal_search" MATCH ?',
            (term,)
        ).fetchone()["n"]
        print(f"{term:20} {count}")
    except Exception as exc:
        print(f"{term:20} ERROR: {type(exc).__name__}: {exc}")

con.close()
