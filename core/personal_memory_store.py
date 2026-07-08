#!/usr/bin/env python3
"""Read-only adapter for Vasuki V2 personal memory."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_DB = Path.home() / "vasuki" / "vasuki_v2" / "data" / "vasuki_personal_memory.db"

class PersonalMemoryStore:
    def __init__(self, db_path: str | Path = DEFAULT_DB):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Personal-memory DB not found: {self.db_path}")

    def connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        return con

    def tables(self) -> list[str]:
        with self.connect() as con:
            return [r["name"] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )]

    def columns(self, table: str) -> list[str]:
        with self.connect() as con:
            return [r["name"] for r in con.execute(f'PRAGMA table_info("{table}")')]

    def integrity(self) -> str:
        with self.connect() as con:
            return con.execute("PRAGMA integrity_check").fetchone()[0]

    def count(self, table: str) -> int:
        with self.connect() as con:
            return con.execute(f'SELECT COUNT(*) AS n FROM "{table}"').fetchone()["n"]

    def _text_columns(self, table: str) -> list[str]:
        cols = self.columns(table)
        preferred = ["content", "text", "chunk_text", "body", "document_text", "title", "path", "source"]
        return [c for c in preferred if c in cols]

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        query = query.strip()
        if not query:
            return []

        tables = self.tables()
        results: list[dict[str, Any]] = []

        # Preferred: SQLite FTS virtual table.
        if "personal_search" in tables:
            try:
                with self.connect() as con:
                    rows = con.execute(
                        'SELECT rowid, * FROM "personal_search" WHERE "personal_search" MATCH ? LIMIT ?',
                        (query, limit),
                    ).fetchall()
                for row in rows:
                    item = dict(row)
                    item["_source_table"] = "personal_search"
                    item["_method"] = "fts"
                    results.append(item)
                if results:
                    return results
            except sqlite3.DatabaseError:
                # FTS syntax/schema differences: safe fallback below.
                pass

        # Fallback: scan likely text columns in personal_chunks.
        if "personal_chunks" not in tables:
            return results

        text_cols = self._text_columns("personal_chunks")
        if not text_cols:
            return results

        where = " OR ".join([f'CAST("{c}" AS TEXT) LIKE ?' for c in text_cols])
        params = [f"%{query}%"] * len(text_cols) + [limit]

        with self.connect() as con:
            rows = con.execute(
                f'SELECT rowid, * FROM "personal_chunks" WHERE {where} LIMIT ?',
                params,
            ).fetchall()

        for row in rows:
            item = dict(row)
            item["_source_table"] = "personal_chunks"
            item["_method"] = "like_fallback"
            results.append(item)

        return results
