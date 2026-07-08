#!/usr/bin/env python3
"""
Vasuki Observation Ledger v1
Stores structured observations derived from explicitly supplied media.
No sensor capture, no upload, no deletion.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.home() / "vasuki"
DB = ROOT / "sense" / "sense_node.db"

def now():
    return datetime.now(timezone.utc).isoformat()

def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("""
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            intake_event_id INTEGER,
            modality TEXT NOT NULL,
            summary TEXT NOT NULL,
            details_json TEXT NOT NULL,
            confidence REAL,
            priority INTEGER NOT NULL DEFAULT 0,
            state TEXT NOT NULL DEFAULT 'NEW',
            FOREIGN KEY(intake_event_id) REFERENCES intake_events(id)
        )
    """)
    con.execute("""
        CREATE INDEX IF NOT EXISTS idx_observations_created
        ON observations(created_at DESC)
    """)
    con.commit()
    return con

def add(args):
    details = json.loads(args.details_json)
    con = connect()
    cur = con.execute("""
        INSERT INTO observations
        (created_at, intake_event_id, modality, summary, details_json, confidence, priority)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        now(),
        args.intake_id,
        args.modality,
        args.summary,
        json.dumps(details, ensure_ascii=False),
        args.confidence,
        args.priority,
    ))
    con.commit()
    print(f"OBSERVATION_CREATED: {cur.lastrowid}")
    con.close()

def recent(args):
    con = connect()
    rows = con.execute("""
        SELECT id, created_at, modality, summary, confidence, priority, state
        FROM observations
        ORDER BY created_at DESC
        LIMIT ?
    """, (args.limit,)).fetchall()
    con.close()

    print("=" * 80)
    print("VASUKI RECENT OBSERVATIONS")
    print("=" * 80)
    for row in rows:
        print(
            f"[{row['id']}] {row['created_at']} "
            f"{row['modality']} priority={row['priority']} "
            f"confidence={row['confidence']} state={row['state']}"
        )
        print(" ", row["summary"])

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("add")
    p.add_argument("--intake-id", type=int)
    p.add_argument("--modality", required=True, choices=["image", "audio", "document", "system"])
    p.add_argument("--summary", required=True)
    p.add_argument("--details-json", default="{}")
    p.add_argument("--confidence", type=float, default=None)
    p.add_argument("--priority", type=int, default=0)
    p.set_defaults(func=add)

    p = sub.add_parser("recent")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=recent)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
