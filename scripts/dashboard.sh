#!/data/data/com.termux/files/usr/bin/bash

OUT="docs/DASHBOARD.md"

echo "# 🚀 Vasuki Live Dashboard" > "$OUT"
echo "" >> "$OUT"
echo "_Generated: $(date)_" >> "$OUT"
echo "" >> "$OUT"

echo "## Repository Metrics" >> "$OUT"
echo "" >> "$OUT"

echo "| Metric | Value |" >> "$OUT"
echo "|--------|------:|" >> "$OUT"

echo "| Repository Size | $(du -sh . | cut -f1) |" >> "$OUT"
echo "| Files | $(find . -type f | wc -l) |" >> "$OUT"
echo "| Directories | $(find . -type d | wc -l) |" >> "$OUT"
echo "| Python Files | $(find . -name '*.py' | wc -l) |" >> "$OUT"
echo "| Python LOC | $(find . -name '*.py' -print0 | xargs -0 cat 2>/dev/null | wc -l) |" >> "$OUT"
echo "| Markdown Files | $(find . -name '*.md' | wc -l) |" >> "$OUT"
echo "| JSON Files | $(find . -name '*.json' | wc -l) |" >> "$OUT"
echo "| SQLite DBs | $(find . -name '*.db' | wc -l) |" >> "$OUT"

TABLES=$(find . -name "*.db" | while read f; do sqlite3 "$f" ".tables" 2>/dev/null | wc -w; done | awk '{s+=$1} END{print s}')
echo "| SQLite Tables | $TABLES |" >> "$OUT"

echo "" >> "$OUT"
echo "## Largest Directories" >> "$OUT"
echo "" >> "$OUT"
echo '```' >> "$OUT"
du -sh * 2>/dev/null | sort -hr | head -10 >> "$OUT"
echo '```' >> "$OUT"

echo "" >> "$OUT"
echo "## Git" >> "$OUT"
echo "" >> "$OUT"
echo '```' >> "$OUT"
echo "Branch: $(git branch --show-current)" >> "$OUT"
echo "Commits: $(git rev-list --count HEAD)" >> "$OUT"
echo '```' >> "$OUT"

echo "" >> "$OUT"
echo "Dashboard updated successfully."
