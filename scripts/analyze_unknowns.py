from pathlib import Path
from collections import Counter

ROOT = Path.home() / "storage" / "shared"

counter = Counter()

for f in ROOT.rglob("*"):
    try:
        if not f.is_file():
            continue

        if f.suffix == "":
            parent = f.parent.name
            counter[parent] += 1

    except:
        pass

print("\nTOP PARENTS OF EXTENSIONLESS FILES\n")

for name,count in counter.most_common(50):
    print(count, name)
