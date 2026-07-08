#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.home() / "vasuki"
OUT = ROOT / "config" / "agent_registry.json"
REPORT = ROOT / "reports" / "agent_registry_audit.txt"

AGENTS = {
    "planner_agent": {
        "role": "Planning and task decomposition",
        "skills": ["task.plan"],
        "permissions": ["database.read", "report.write"]
    },
    "search_agent": {
        "role": "Personal-memory and file retrieval",
        "skills": ["memory.search"],
        "permissions": ["database.read"]
    },
    "memory_agent": {
        "role": "Memory validation, provenance, and database inspection",
        "skills": ["database.audit"],
        "permissions": ["database.read", "report.write"]
    },
    "filesystem_agent": {
        "role": "File discovery, classification, and normalization proposals",
        "skills": ["files.normalize"],
        "permissions": ["data.read", "normalized.write"]
    },
    "backup_agent": {
        "role": "Database snapshot creation and backup verification",
        "skills": ["backup.create"],
        "permissions": ["database.read", "backup.write"]
    },
    "executor_agent": {
        "role": "Approved action execution only",
        "skills": ["task.execute"],
        "permissions": ["shell.execute", "log.write"]
    },
    "reasoning_agent": {
        "role": "Evidence-based critique and decision support",
        "skills": ["task.critique"],
        "permissions": ["database.read", "report.write"]
    },
    "device_agent": {
        "role": "Device health and runtime inspection",
        "skills": ["device.inspect"],
        "permissions": ["report.write"]
    },
    "project_agent": {
        "role": "Repository inventory and project-state analysis",
        "skills": ["project.audit"],
        "permissions": ["data.read", "report.write"]
    },
    "code_agent": {
        "role": "Code analysis and proposed patches",
        "skills": ["code.review"],
        "permissions": ["data.read", "report.write"]
    }
}

def locate_agent(name: str) -> list[str]:
    candidates = [
        ROOT / f"{name}.py",
        ROOT / "agents" / f"{name}.py",
        ROOT / "scripts" / f"{name}.py"
    ]
    return [str(path.relative_to(ROOT)) for path in candidates if path.exists()]

def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(timezone.utc).isoformat()
    registry = {
        "version": "1.0",
        "generated_at": generated_at,
        "agents": []
    }

    lines = [
        "=" * 80,
        "VASUKI AGENT REGISTRY AUDIT v1",
        f"Generated: {generated_at}",
        "=" * 80,
        ""
    ]

    found_count = 0
    for name, spec in AGENTS.items():
        locations = locate_agent(name)
        exists = bool(locations)
        found_count += int(exists)

        entry = {
            "id": name,
            "role": spec["role"],
            "skills": spec["skills"],
            "permissions": spec["permissions"],
            "locations": locations,
            "status": "AVAILABLE" if exists else "DECLARED_NOT_FOUND",
            "execution_policy": (
                "requires_approved_task_id"
                if name == "executor_agent"
                else "read_or_propose_only"
            )
        }
        registry["agents"].append(entry)

        lines.extend([
            f"AGENT: {name}",
            f"  status      : {entry['status']}",
            f"  locations   : {', '.join(locations) if locations else 'none'}",
            f"  role        : {entry['role']}",
            f"  skills      : {', '.join(entry['skills'])}",
            f"  permissions : {', '.join(entry['permissions'])}",
            f"  policy      : {entry['execution_policy']}",
            ""
        ])

    lines.extend([
        "-" * 80,
        f"SUMMARY: {found_count}/{len(AGENTS)} declared agents found",
        f"REGISTRY: {OUT}",
        "=" * 80
    ])

    OUT.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))

if __name__ == "__main__":
    main()
