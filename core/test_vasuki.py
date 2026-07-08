#!/usr/bin/env python3
from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.home() / "vasuki"
CONTROL_DB = ROOT / "database" / "vasuki_control.db"
SKILLS = ROOT / "skills" / "registry.json"
AGENTS = ROOT / "config" / "agent_registry.json"
REPORTS = ROOT / "reports"

results = []

def check(name: str, passed: bool, detail: str) -> None:
    results.append({"name": name, "passed": passed, "detail": detail})
    marker = "PASS" if passed else "FAIL"
    print(f"{marker}: {name}")
    print(f"  {detail}")

def main() -> int:
    print("=" * 80)
    print("VASUKI SYSTEM TEST v1")
    print("Time:", datetime.now(timezone.utc).isoformat())
    print("=" * 80)

    # 1. Required control-plane files
    check("skills registry exists", SKILLS.exists(), str(SKILLS))
    check("agent registry exists", AGENTS.exists(), str(AGENTS))
    check("control database exists", CONTROL_DB.exists(), str(CONTROL_DB))

    # 2. JSON validity
    try:
        skills = json.loads(SKILLS.read_text(encoding="utf-8"))
        check("skills registry JSON", True, f"{len(skills.get('skills', []))} skills loaded")
    except Exception as exc:
        skills = {}
        check("skills registry JSON", False, repr(exc))

    try:
        agents = json.loads(AGENTS.read_text(encoding="utf-8"))
        check("agent registry JSON", True, f"{len(agents.get('agents', []))} agents loaded")
    except Exception as exc:
        agents = {}
        check("agent registry JSON", False, repr(exc))

    # 3. Agent-to-skill wiring
    try:
        skill_owners = {x["id"]: x["owner"] for x in skills["skills"]}
        agent_map = {x["id"]: x for x in agents["agents"]}
        missing = [
            f"{skill_id} -> {owner}"
            for skill_id, owner in skill_owners.items()
            if owner not in agent_map or skill_id not in agent_map[owner]["skills"]
        ]
        check(
            "agent-to-skill wiring",
            not missing,
            "all declared skills wired" if not missing else "; ".join(missing)
        )
    except Exception as exc:
        check("agent-to-skill wiring", False, repr(exc))

    # 4. Control database integrity and Council history
    try:
        con = sqlite3.connect(CONTROL_DB)
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        task_table = con.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='agent_tasks'
        """).fetchone()
        task_count = con.execute("SELECT COUNT(*) FROM agent_tasks").fetchone()[0]
        con.close()

        check("control DB integrity", integrity == "ok", integrity)
        check("Council task table", task_table is not None, f"agent_tasks rows: {task_count}")
    except Exception as exc:
        check("control DB integrity", False, repr(exc))
        check("Council task table", False, repr(exc))

    # 5. Required scripts
    required = [
        ROOT / "core" / "task_council.py",
        ROOT / "core" / "validate_skills.py",
        ROOT / "core" / "build_agent_registry.py",
        ROOT / "core" / "validate_agent_wiring.py",
    ]
    missing_scripts = [str(x.relative_to(ROOT)) for x in required if not x.exists()]
    check(
        "core automation scripts",
        not missing_scripts,
        "all required scripts found" if not missing_scripts else ", ".join(missing_scripts)
    )

    # 6. Non-destructive search capability probe
    search_script = ROOT / "scripts" / "search.py"
    if not search_script.exists():
        check("memory search script exists", False, str(search_script))
    else:
        try:
            run = subprocess.run(
                [sys.executable, str(search_script), "normalization"],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=30
            )
            output = run.stdout.strip().replace("\n", " ")[:500]
            check(
                "memory search capability",
                run.returncode == 0,
                f"exit={run.returncode}; output={output or '[no output]'}"
            )
        except Exception as exc:
            check("memory search capability", False, repr(exc))

    # 7. Write report
    REPORTS.mkdir(exist_ok=True)
    report = REPORTS / "vasuki_system_test_latest.json"
    report.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": results
    }, indent=2), encoding="utf-8")

    passed = sum(x["passed"] for x in results)
    total = len(results)
    print("=" * 80)
    print(f"RESULT: {passed}/{total} checks passed")
    print("REPORT:", report)
    print("=" * 80)

    return 0 if passed == total else 1

if __name__ == "__main__":
    raise SystemExit(main())
