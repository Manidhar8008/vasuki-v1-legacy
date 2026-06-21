import os
from ingest import insert_file

ROOT = "/storage/emulated/0/Download"

for root, dirs, files in os.walk(ROOT):
    for f in files:
        path = os.path.join(root, f)
        insert_file(path)

print("\nMEMORY COLLECTION COMPLETE")
