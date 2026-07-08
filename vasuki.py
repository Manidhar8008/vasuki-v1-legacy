#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.personal_memory_store import DEFAULT_DB, PersonalMemoryStore

def compact(value, max_len=500):
    text = str(value)
    return text if len(text) <= max_len else text[:max_len] + "..."

def command_status(_args):
    store = PersonalMemoryStore()
    print("VASUKI RETRIEVAL STATUS")
    print("DB:", store.db_path)
    print("Integrity:", store.integrity())
    for table in ["personal_documents", "personal_chunks", "personal_search"]:
        if table in store.tables():
            print(f"{table}: {store.count(table)}")

def command_search(args):
    store = PersonalMemoryStore(args.db or DEFAULT_DB)
    results = store.search(args.query, args.limit)

    if args.json:
        print(json.dumps({
            "query": args.query,
            "database": str(store.db_path),
            "result_count": len(results),
            "results": results
        }, indent=2, default=str))
        return

    print("=" * 72)
    print("VASUKI PERSONAL MEMORY SEARCH")
    print("Query:", args.query)
    print("Database:", store.db_path)
    print("Results:", len(results))
    print("=" * 72)

    for i, row in enumerate(results, 1):
        print(f"\n[{i}] method={row.pop('_method', 'unknown')} table={row.pop('_source_table', 'unknown')}")
        for key, value in row.items():
            print(f"{key}: {compact(value)}")

def main():
    parser = argparse.ArgumentParser(prog="vasuki.py")
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status")
    status.set_defaults(func=command_status)

    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=10)
    search.add_argument("--json", action="store_true")
    search.add_argument("--db", help="Override database path; read-only only.")
    search.set_defaults(func=command_search)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
