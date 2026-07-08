#!/usr/bin/env python3
"""
Vasuki Sense Node v1: media discovery and immutable intake queue.
No recording. No upload. No deletion. No modification of source files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.home() / "vasuki"
SENSE = ROOT / "sense"
DB = SENSE / "sense_node.db"
DEFAULT_MEDIA_ROOT = Path.home() / "storage" / "shared"

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
DOC_EXT = {".pdf"}
AUDIO_EXT = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".opus", ".flac"}

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def kind_for(path: Path) -> str | None:
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXT:
        return "image"
    if suffix in DOC_EXT:
        return "document"
    if suffix in AUDIO_EXT:
        return "audio"
    return None

def connect() -> sqlite3.Connection:
    SENSE.mkdir(exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS intake_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            source_path TEXT NOT NULL UNIQUE,
            media_kind TEXT NOT NULL,
            mime_type TEXT,
            size_bytes INTEGER NOT NULL,
            modified_at TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'QUEUED',
            processor TEXT,
            observation_json TEXT,
            error_text TEXT
        )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_intake_status ON intake_events(status)")
    con.commit()
    return con

def scan(root: Path, limit: int | None) -> int:
    if not root.exists():
        raise FileNotFoundError(
            f"Media root not found: {root}. Run termux-setup-storage first."
        )

    con = connect()
    queued = 0
    skipped = 0

    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            path = Path(dirpath) / filename
            media_kind = kind_for(path)
            if media_kind is None:
                continue

            try:
                stat = path.stat()
                con.execute("""
                    INSERT OR IGNORE INTO intake_events
                    (created_at, source_path, media_kind, mime_type, size_bytes,
                     modified_at, sha256, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'QUEUED')
                """, (
                    now(),
                    str(path),
                    media_kind,
                    mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                    stat.st_size,
                    datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                    sha256(path),
                ))
                if con.total_changes:
                    queued += 1
                else:
                    skipped += 1

                if limit and queued >= limit:
                    con.commit()
                    con.close()
                    print(f"Queued: {queued}; already known: {skipped}")
                    return queued
            except (OSError, PermissionError) as exc:
                print(f"SKIP: {path} -> {exc}")

    con.commit()
    con.close()
    print(f"Queued: {queued}; already known: {skipped}")
    return queued

def status() -> None:
    con = connect()
    rows = con.execute("""
        SELECT media_kind, status, COUNT(*) AS n
        FROM intake_events
        GROUP BY media_kind, status
        ORDER BY media_kind, status
    """).fetchall()
    con.close()

    print("=" * 72)
    print("VASUKI SENSE NODE STATUS")
    print("Database:", DB)
    print("=" * 72)
    if not rows:
        print("No intake events.")
        return
    for media_kind, state, count in rows:
        print(f"{media_kind:10} {state:12} {count}")

def main() -> None:
    parser = argparse.ArgumentParser(prog="sense_queue.py")
    sub = parser.add_subparsers(dest="command", required=True)

    scan_cmd = sub.add_parser("scan")
    scan_cmd.add_argument("--root", type=Path, default=DEFAULT_MEDIA_ROOT)
    scan_cmd.add_argument("--limit", type=int, default=None)

    sub.add_parser("status")
    args = parser.parse_args()

    if args.command == "scan":
        scan(args.root, args.limit)
    else:
        status()

if __name__ == "__main__":
    main()
