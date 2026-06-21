#!/usr/bin/env python3

import argparse
from vasuki.core.db import VasukiDB
from vasuki.core.ask_engine import AskEngine


def main():
    parser = argparse.ArgumentParser(description="Vasuki Ask System")
    
    parser.add_argument("query", help="Search query")
    parser.add_argument("--mode", choices=["memory", "entity", "all", "sql"], default="memory")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--raw-sql", help="Run raw SQL query (advanced)")

    args = parser.parse_args()

    db = VasukiDB("data/vasuki.db")
    engine = AskEngine(db)

    if args.raw_sql:
        result = db.execute_raw(args.raw_sql)
        print(result)
        return

    results = engine.ask(
        query=args.query,
        mode=args.mode,
        limit=args.limit
    )

    engine.pretty_print(results)


if __name__ == "__main__":
    main()
