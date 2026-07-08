#!/usr/bin/env python3

import os
import time
import subprocess
from datetime import datetime

def sh(cmd):
    return subprocess.getoutput(cmd)

while True:
    with open("docs/DASHBOARD.md","w") as f:
        f.write("# 🚀 Vasuki Live Dashboard\n\n")
        f.write(f"Generated: {datetime.now()}\n\n")
        f.write("## Repository Metrics\n\n")
        f.write(f"- Size: {sh('du -sh . | cut -f1')}\n")
        f.write(f"- Files: {sh('find . -type f | wc -l')}\n")
        f.write(f"- Directories: {sh('find . -type d | wc -l')}\n")
        f.write(f"- Python Files: {sh(\"find . -name '*.py' | wc -l\")}\n")
        f.write(f"- Markdown Files: {sh(\"find . -name '*.md' | wc -l\")}\n")
        f.write(f"- SQLite DBs: {sh(\"find . -name '*.db' | wc -l\")}\n")
        f.write(f"- Git Branch: {sh('git branch --show-current')}\n")
        f.write(f"- Git Commits: {sh('git rev-list --count HEAD')}\n")

    print("Dashboard Updated")
    time.sleep(60)
