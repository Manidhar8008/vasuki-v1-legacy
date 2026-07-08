#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path.home() / "vasuki"
AGENTS = ROOT / "config" / "agent_registry.json"
SKILLS = ROOT / "skills" / "registry.json"

agent_registry = json.loads(AGENTS.read_text(encoding="utf-8"))
skill_registry = json.loads(SKILLS.read_text(encoding="utf-8"))

skill_owners = {skill["id"]: skill["owner"] for skill in skill_registry["skills"]}
agents = {agent["id"]: agent for agent in agent_registry["agents"]}

errors = []
print("=" * 72)
print("VASUKI AGENT ↔ SKILL WIRING VALIDATOR v1")
print("=" * 72)

for skill_id, owner in skill_owners.items():
    agent = agents.get(owner)
    if not agent:
        errors.append(f"{skill_id}: owner '{owner}' missing from agent registry")
        continue

    if skill_id not in agent["skills"]:
        errors.append(f"{skill_id}: not declared under {owner}.skills")
        continue

    print(f"PASS: {skill_id} -> {owner} -> {agent['status']}")

print("-" * 72)
if errors:
    print("FAIL:")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

print("PASS: all skill owners are wired to declared agents")
