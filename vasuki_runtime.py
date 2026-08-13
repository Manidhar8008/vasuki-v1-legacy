#!/usr/bin/env python3

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path.home() / "vasuki"

# Canonical runtime database.
DB = ROOT / "vasuki.db"

# Existing V2 personal-memory source.
PERSONAL_DB = ROOT / "vasuki_v2" / "data" / "vasuki_personal_memory.db"

# Existing control plane.
CONTROL_DB = ROOT / "database" / "vasuki_control.db"


def now():
    return datetime.now(timezone.utc).isoformat()


def connect():
    con = sqlite3.connect(DB, timeout=30)
    con.row_factory = sqlite3.Row
    return con


def init_schema(con):
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS system_identity (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_id TEXT,
            memory_type TEXT NOT NULL,
            title TEXT,
            content TEXT NOT NULL,
            importance INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source, source_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_id TEXT,
            title TEXT,
            content TEXT NOT NULL,
            content_type TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source, source_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS runtime_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            detail TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS subsystem_registry (
            name TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            description TEXT,
            updated_at TEXT
        )
    """)

    con.commit()


def register_subsystems(con):
    subsystems = {
        "queue": "File discovery and durable processing queue",
        "processor": "Content extraction and ingestion",
        "memory": "Canonical runtime memories",
        "knowledge": "Canonical runtime knowledge",
        "personal_memory_source": "V2 personal-memory source",
        "snapshots": "Snapshot and change history",
        "task_council": "Controlled planning and safety layer",
    }

    for name, description in subsystems.items():
        con.execute("""
            INSERT INTO subsystem_registry
                (name, status, description, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                status=excluded.status,
                description=excluded.description,
                updated_at=excluded.updated_at
        """, (
            name,
            "registered",
            description,
            now(),
        ))

    con.commit()


def import_extracted_text(con):
    cur = con.cursor()

    exists = cur.execute("""
        SELECT 1
        FROM sqlite_master
        WHERE type='table' AND name='extracted_text'
    """).fetchone()

    if not exists:
        return 0

    rows = cur.execute("""
        SELECT
            file_path,
            file_type,
            content
        FROM extracted_text
        WHERE content IS NOT NULL
          AND length(trim(content)) > 0
    """).fetchall()

    imported = 0

    for row in rows:
        source_id = row["file_path"]

        cur.execute("""
            INSERT INTO knowledge
                (source, source_id, title, content, content_type)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(source, source_id) DO UPDATE SET
                content=excluded.content,
                content_type=excluded.content_type
        """, (
            "extracted_text",
            source_id,
            Path(source_id).name,
            row["content"],
            row["file_type"],
        ))

        imported += 1

    con.commit()
    return imported


def import_personal_memory(con):
    """
    Import the existing V2 personal-memory database into the
    canonical runtime database.

    This adapter is deliberately schema-tolerant:
    - discovers tables dynamically
    - discovers columns dynamically
    - never assumes rowid exists in sqlite3.Row
    - never crashes the entire runtime because the V2 source
      has a different schema
    """

    if not PERSONAL_DB.exists():
        print("Personal memory DB not found:", PERSONAL_DB)
        return 0

    try:
        source = sqlite3.connect(
            f"file:{PERSONAL_DB}?mode=ro",
            uri=True,
        )
        source.row_factory = sqlite3.Row
    except Exception as exc:
        print("Could not open personal memory DB:", exc)
        return 0

    imported = 0

    try:
        tables = [
            row["name"]
            for row in source.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                  AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """).fetchall()
        ]

        print("Personal-memory source tables:", tables)

        for table in tables:

            try:
                columns = [
                    row["name"]
                    for row in source.execute(
                        f'PRAGMA table_info("{table}")'
                    ).fetchall()
                ]
            except Exception as exc:
                print(f"Skipping {table}: schema error: {exc}")
                continue

            if not columns:
                continue

            # Look for columns likely to contain actual information.
            content_columns = [
                c for c in (
                    "content",
                    "text",
                    "chunk_text",
                    "body",
                    "document_text",
                    "memory",
                    "description",
                    "summary",
                    "value",
                    "title",
                    "path",
                    "source",
                )
                if c in columns
            ]

            if not content_columns:
                print(
                    f"Skipping {table}: "
                    f"no recognizable content columns"
                )
                continue

            expressions = [
                f'COALESCE(CAST("{c}" AS TEXT), \'\')'
                for c in content_columns
            ]

            text_expr = " || '\n' || ".join(expressions)

            try:
                rows = source.execute(
                    f"""
                    SELECT *
                    FROM "{table}"
                    WHERE length(trim({text_expr})) > 0
                    """
                ).fetchall()
            except Exception as exc:
                print(f"Skipping {table}: read error: {exc}")
                continue

            print(
                f"Reading {table}: "
                f"{len(rows)} candidate records"
            )

            for index, row in enumerate(rows):

                try:
                    parts = []

                    for column in content_columns:
                        value = row[column]

                        if value is not None:
                            value = str(value).strip()

                            if value:
                                parts.append(value)

                    content = "\n".join(parts).strip()

                    if not content:
                        continue

                    # Use a deterministic source identifier.
                    # Do NOT depend on SQLite rowid.
                    source_id = f"{table}:{index}"

                    title = (
                        str(row["title"]).strip()
                        if "title" in row.keys()
                        and row["title"] is not None
                        else table
                    )

                    con.execute("""
                        INSERT INTO memories
                            (
                                source,
                                source_id,
                                memory_type,
                                title,
                                content,
                                importance
                            )
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(source, source_id)
                        DO UPDATE SET
                            content=excluded.content,
                            title=excluded.title
                    """, (
                        f"vasuki_v2.{table}",
                        source_id,
                        "personal",
                        title[:500],
                        content,
                        2,
                    ))

                    imported += 1

                except Exception as exc:
                    print(
                        f"Skipping record {table}:{index}: {exc}"
                    )

    finally:
        source.close()

    con.commit()

    print(
        "Personal memory import complete:",
        imported
    )

    return imported

def status(con):
    print("\n==============================")
    print("       VASUKI RUNTIME")
    print("==============================")
    print("DB:", DB)
    print("Time:", now())

    print("\nINTEGRITY:")
    print(con.execute("PRAGMA integrity_check").fetchone()[0])

    print("\nTABLES:")
    tables = con.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """).fetchall()

    for row in tables:
        name = row["name"]
        try:
            count = con.execute(
                f'SELECT COUNT(*) FROM "{name}"'
            ).fetchone()[0]
            print(f"  {name}: {count}")
        except Exception:
            print(f"  {name}: ?")

    print("\nSUBSYSTEMS:")
    rows = con.execute("""
        SELECT name, status
        FROM subsystem_registry
        ORDER BY name
    """).fetchall()

    for row in rows:
        print(f"  {row['name']}: {row['status']}")


def search(con, query):
    query = query.strip()

    if not query:
        return

    print(f"\n=== VASUKI SEARCH: {query} ===")

    found = False

    for table, columns in (
        (
            "memories",
            ["title", "content"],
        ),
        (
            "knowledge",
            ["title", "content"],
        ),
    ):
        for column in columns:
            try:
                rows = con.execute(
                    f"""
                    SELECT *
                    FROM "{table}"
                    WHERE CAST("{column}" AS TEXT) LIKE ?
                    LIMIT 10
                    """,
                    (f"%{query}%",),
                ).fetchall()

                for row in rows:
                    found = True

                    print("\nSOURCE:", table)

                    if "title" in row.keys():
                        print("TITLE:", row["title"])

                    print(
                        "CONTENT:",
                        (row["content"] or "")[:1200]
                    )

            except sqlite3.Error:
                pass

    if not found:
        print("No matching memory or knowledge found.")


def ingest(con):
    print("\n=== INGEST ===")

    extracted = import_extracted_text(con)
    personal = import_personal_memory(con)

    con.execute("""
        INSERT INTO runtime_events(event_type, detail)
        VALUES (?, ?)
    """, (
        "ingest",
        f"knowledge={extracted}, personal={personal}",
    ))

    con.commit()

    print("Extracted knowledge imported:", extracted)
    print("Personal memory imported:", personal)


def handle(con, command):
    command = command.strip()

    if not command:
        return True

    if command == "quit":
        return False

    if command == "status":
        status(con)
        return True

    if command == "ingest":
        ingest(con)
        return True

    if command == "recent":
        rows = con.execute("""
            SELECT source, title, created_at
            FROM memories
            UNION ALL
            SELECT source, title, created_at
            FROM knowledge
            ORDER BY created_at DESC
            LIMIT 20
        """).fetchall()

        print("\n=== RECENT KNOWLEDGE ===")
        for row in rows:
            print(
                f"{row['created_at']} | "
                f"{row['source']} | "
                f"{row['title']}"
            )

        return True

    if command.startswith("search "):
        search(con, command[7:])
        return True

    # Treat normal text as a search request.
    search(con, command)
    return True


def main():
    con = connect()

    init_schema(con)
    register_subsystems(con)

    # One-time/current import pass.
    ingest(con)

    status(con)

    print("""
Commands:

  status
  ingest
  recent
  search <query>
  quit

Normal text is also treated as a search query.
""")

    while True:
        try:
            command = input("\nVASUKI> ")

            if not handle(con, command):
                break

        except KeyboardInterrupt:
            print("\nStopping Vasuki.")
            break

        except EOFError:
            break

        except Exception as exc:
            print("RUNTIME ERROR:", exc)

    con.close()


if __name__ == "__main__":
    main()
