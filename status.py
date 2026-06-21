import sqlite3
import shutil
from pathlib import Path

BASE = Path.home() / "vasuki"
DB = BASE / "data" / "vasuki.db"

print("=" * 40)
print("VASUKI STATUS")
print("=" * 40)

print("Database:", DB.exists())

if DB.exists():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    try:
        cur.execute("SELECT COUNT(*) FROM files")
        files = cur.fetchone()[0]
    except:
        files = 0

    try:
        cur.execute("SELECT COUNT(*) FROM memories")
        memories = cur.fetchone()[0]
    except:
        memories = 0

    try:
        cur.execute("SELECT COUNT(*) FROM conversations")
        conv = cur.fetchone()[0]
    except:
        conv = 0

    conn.close()

    print("Files Indexed :", files)
    print("Memories      :", memories)
    print("Conversations :", conv)

usage = shutil.disk_usage("/storage/emulated/0")

print()
print("Storage")
print("Used :", round((usage.total-usage.free)/1024**3,2),"GB")
print("Free :", round(usage.free/1024**3,2),"GB")
print("Total:", round(usage.total/1024**3,2),"GB")

print()
print("Model Directory")

models = list((BASE/"models").glob("*.gguf"))

if models:
    for m in models:
        print("✓",m.name)
else:
    print("No GGUF models installed")
