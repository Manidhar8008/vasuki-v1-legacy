#!/usr/bin/env python3
"""
VASUKI Task Council v1
A controlled multi-agent review workflow.
No agent may execute shell commands directly.
"""

from __future__ import annotations
import json
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.home() / "vasuki"
DB = ROOT / "database" / "vasuki_control.db"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

def now():
    return datetime.now(timezone.utc).isoformat()

def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("""
        CREATE TABLE IF NOT EXISTS agent_tasks (
            task_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            goal TEXT NOT NULL,
            status TEXT NOT NULL,
            plan_json TEXT NOT NULL,
            critique_json TEXT NOT NULL,
            decision_json TEXT NOT NULL
        )
    """)
    con.commit()
    return con

def planner(goal: str) -> dict:
    return {
        "agent": "planner",
        "goal": goal,
        "steps": [
            "Identify relevant source files and database records",
            "Produce a non-destructive proposed action",
            "Request independent critique",
            "Require verification criteria before execution"
        ],
        "requires_human_approval": True
    }

def critic(plan: dict) -> dict:
    risks = [
        "Multiple Vasuki databases exist; do not assume one is canonical.",
        "No destructive command may run without a backup and explicit approval.",
        "Every claim must identify source files, SQL query, or log evidence.",
        "A proposal must be idempotent: rerunning it must not duplicate data."
    ]
    return {
        "agent": "critic",
        "verdict": "REVISE",
        "risks": risks,
        "required_changes": [
            "Specify the database path explicitly.",
            "Specify rollback or backup behavior.",
            "Specify a verification command."
        ],
        "plan_reviewed": plan
    }

def safety_gate(plan: dict, critique: dict) -> dict:
    approved = (
        plan.get("requires_human_approval") is True
        and critique.get("verdict") in {"REVISE", "APPROVE"}
    )
    return {
        "agent": "safety_gate",
        "status": "PENDING_HUMAN_APPROVAL" if approved else "BLOCKED",
        "reason": "Execution is disabled in Council v1. This run creates an auditable proposal only."
    }

def main():
    if len(sys.argv) < 2:
        print('Usage: python3 core/task_council.py "your goal"')
        raise SystemExit(2)

    goal = " ".join(sys.argv[1:])
    task_id = f"vasuki-{uuid.uuid4().hex[:12]}"

    plan = planner(goal)
    critique = critic(plan)
    decision = safety_gate(plan, critique)

    record = {
        "task_id": task_id,
        "created_at": now(),
        "goal": goal,
        "plan": plan,
        "critique": critique,
        "decision": decision
    }

    con = connect()
    con.execute("""
        INSERT INTO agent_tasks
        (task_id, created_at, goal, status, plan_json, critique_json, decision_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        task_id, record["created_at"], goal, decision["status"],
        json.dumps(plan, indent=2),
        json.dumps(critique, indent=2),
        json.dumps(decision, indent=2)
    ))
    con.commit()
    con.close()

    report = REPORTS / f"{task_id}.json"
    report.write_text(json.dumps(record, indent=2), encoding="utf-8")

    print("=" * 72)
    print("VASUKI TASK COUNCIL v1")
    print("=" * 72)
    print("Task ID:", task_id)
    print("Status :", decision["status"])
    print("Report :", report)
    print("\nPlanner proposal:")
    print(json.dumps(plan, indent=2))
    print("\nCritic review:")
    print(json.dumps(critique, indent=2))
    print("\nDecision:")
    print(json.dumps(decision, indent=2))

if __name__ == "__main__":
    main()
