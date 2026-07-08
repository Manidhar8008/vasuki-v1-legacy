#!/usr/bin/env python3
from pathlib import Path
import sqlite3

DB = Path.home() / "vasuki" / "vasuki_v2" / "data" / "vasuki_personal_memory.db"

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
cur = con.cursor()

print("=" * 80)
print("VASUKI PERSONAL MEMORY SCHEMA INSPECTION v1")
print("DATABASE:", DB)
print("=" * 80)

tables = [
    "personal_documents",
    "personal_chunks",
    "personal_search"
]

for table in tables:
    print(f"\nTABLE: {table}")
    print("-" * 80)

    columns = cur.execute(f'PRAGMA table_info("{table}")').fetchall()
    for col in columns:
        print(f"  {col[1]} | {col[2]} | notnull={col[3]} | pk={col[5]}")

    print("\nSAMPLE ROW:")
    try:
        row = cur.execute(f'SELECT * FROM "{table}" LIMIT 1').fetchone()
        if row is None:
            print("  [empty]")
        else:
            names = [x[0] for x in cur.description]
            for name, value in zip(names, row):
                text = str(value)
                if len(text) > 500:
                    text = text[:500] + "..."
                print(f"  {name}: {text}")
    except Exception as exc:
        print("  ERROR:", type(exc).__name__, exc)

print("\n" + "=" * 80)
con.close()
