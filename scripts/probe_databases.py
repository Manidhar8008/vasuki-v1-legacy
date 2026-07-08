#!/usr/bin/env python3
from pathlib import Path
import sqlite3

ROOT = Path.home() / "vasuki"

DATABASES = [
    ROOT / "data" / "vasuki.db",
    ROOT / "vasuki.db",
    ROOT / "scripts" / "vasuki.db",
    ROOT / "vasuki_v2" / "data" / "vasuki.db",
    ROOT / "vasuki_v2" / "data" / "vasuki_source_memory.db",
    ROOT / "vasuki_v2" / "data" / "vasuki_personal_memory.db",
]

print("=" * 80)
print("VASUKI READ-ONLY DATABASE PROBE v1")
print("=" * 80)

for db in DATABASES:
    print(f"\nDATABASE: {db}")
    if not db.exists():
        print("  STATUS: MISSING")
        continue

    print(f"  SIZE: {db.stat().st_size / (1024 * 1024):.2f} MB")

    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        cur = con.cursor()

        integrity = cur.execute("PRAGMA integrity_check").fetchone()[0]
        print(f"  INTEGRITY: {integrity}")

        tables = cur.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """).fetchall()

        print("  TABLES:")
        for (table,) in tables:
            try:
                count = cur.execute(
                    f'SELECT COUNT(*) FROM "{table}"'
                ).fetchone()[0]
                print(f"    - {table}: {count}")
            except Exception as exc:
                print(f"    - {table}: COUNT_ERROR: {exc}")

        con.close()

    except Exception as exc:
        print(f"  STATUS: UNUSABLE")
        print(f"  ERROR: {type(exc).__name__}: {exc}")

print("\n" + "=" * 80)
