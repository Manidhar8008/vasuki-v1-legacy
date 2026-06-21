from pathlib import Path
from collections import Counter
from datetime import datetime

ROOT = Path.home() / "storage" / "shared"

exts = Counter()
folders = Counter()
years = Counter()

total = 0

for p in ROOT.rglob("*"):

    try:

        if not p.is_file():
            continue

        total += 1

        exts[p.suffix.lower()] += 1

        if len(p.parts) > 8:
            folders[p.parts[8]] += 1

        year = datetime.fromtimestamp(
            p.stat().st_mtime
        ).year

        years[year] += 1

    except:
        pass

print("\nTOTAL FILES:", total)

print("\nTOP EXTENSIONS")
for k,v in exts.most_common(30):
    print(v, k)

print("\nTOP FOLDERS")
for k,v in folders.most_common(30):
    print(v, k)

print("\nFILES BY YEAR")
for y in sorted(years):
    print(y, years[y])
