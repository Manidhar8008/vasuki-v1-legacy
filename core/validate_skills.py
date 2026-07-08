#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path.home() / "vasuki"
REGISTRY = ROOT / "skills" / "registry.json"

VALID_PERMISSIONS = {
    "database.read",
    "database.write",
    "data.read",
    "normalized.write",
    "backup.write",
    "report.write",
    "log.write",
    "shell.execute"
}

REQUIRED_FIELDS = {
    "id",
    "owner",
    "description",
    "inputs",
    "outputs",
    "permissions",
    "verification"
}

def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)

def main() -> None:
    if not REGISTRY.exists():
        fail(f"Registry missing: {REGISTRY}")

    try:
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON: {exc}")

    if registry.get("version") != "1.0":
        fail("Unsupported or missing registry version")

    skills = registry.get("skills")
    if not isinstance(skills, list) or not skills:
        fail("'skills' must be a non-empty list")

    seen_ids = set()
    print("=" * 72)
    print("VASUKI SKILL REGISTRY VALIDATOR v1")
    print("=" * 72)

    for index, skill in enumerate(skills, start=1):
        if not isinstance(skill, dict):
            fail(f"Skill #{index} is not an object")

        missing = REQUIRED_FIELDS - set(skill)
        if missing:
            fail(f"Skill #{index} missing fields: {sorted(missing)}")

        skill_id = skill["id"]
        if not isinstance(skill_id, str) or "." not in skill_id:
            fail(f"Invalid skill id: {skill_id!r}")

        if skill_id in seen_ids:
            fail(f"Duplicate skill id: {skill_id}")
        seen_ids.add(skill_id)

        permissions = skill["permissions"]
        if not isinstance(permissions, list):
            fail(f"{skill_id}: permissions must be a list")

        unknown = set(permissions) - VALID_PERMISSIONS
        if unknown:
            fail(f"{skill_id}: unknown permissions: {sorted(unknown)}")

        owner = skill["owner"]
        owner_file = ROOT / f"{owner}.py"
        agent_file = ROOT / "agents" / f"{owner}.py"

        owner_exists = owner_file.exists() or agent_file.exists()

        print(f"\n[{index}] {skill_id}")
        print(f"  owner       : {owner}")
        print(f"  owner exists: {'YES' if owner_exists else 'NO — registry contract only'}")
        print(f"  permissions : {', '.join(permissions)}")
        print(f"  verify      : {skill['verification']}")

    print("\n" + "=" * 72)
    print(f"PASS: {len(skills)} skills validated")
    print("=" * 72)

if __name__ == "__main__":
    main()
