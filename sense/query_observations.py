#!/usr/bin/env python3
"""
Vasuki Observation Query v1
Read-only search over the Sense Node observation ledger.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

DB = Path.home() / "vasuki" / "sense" / "sense_node.db"

def main():
    parser = argparse.ArgumentParser(
        description="Read-only search of Vasuki Sense observations."
    )
    parser.add_argument("query", nargs="*", help="Words to search in summaries/details")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--state", default=None)
    parser.add_argument("--modality", default=None)
    parser.add_argument("--include-superseded", action="store_true")
    args = parser.parse_args()

    if not DB.is_file():
        raise SystemExit(f"ERROR: Sense database not found: {DB}")

    query = " ".join(args.query).strip()
    limit = max(1, min(args.limit, 100))

    clauses = []
    values = []

    if query:
        clauses.append("(summary LIKE ? OR details_json LIKE ?)")
        values.extend([f"%{query}%", f"%{query}%"])

    if args.state:
        clauses.append("state = ?")
        values.append(args.state)

    if args.modality:
        clauses.append("modality = ?")
        values.append(args.modality)

    if not args.include_superseded:
        clauses.append("state != 'SUPERSEDED'")

    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    sql = f"""
        SELECT id, created_at, modality, summary, details_json,
               confidence, priority, state
        FROM observations
        {where}
        ORDER BY created_at DESC
        LIMIT ?
    """
    values.append(limit)

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = con.execute(sql, values).fetchall()
    con.close()

    print("=" * 80)
    print("VASUKI OBSERVATION SEARCH — READ ONLY")
    print(f"Database: {DB}")
    print(f"Query: {query or '[all]'}")
    print(f"Results: {len(rows)}")
    print("=" * 80)

    for row in rows:
        print(f"\n[{row['id']}] {row['created_at']}")
        print(f"  modality : {row['modality']}")
        print(f"  state    : {row['state']}")
        print(f"  priority : {row['priority']}")
        print(f"  summary  : {row['summary']}")
        try:
            details = json.loads(row["details_json"])
            if "transcript_file" in details:
                print(f"  transcript_file: {details['transcript_file']}")
            if "audio" in details:
                print(f"  audio: {details['audio']}")
        except (TypeError, json.JSONDecodeError):
            pass

if __name__ == "__main__":
    main()
