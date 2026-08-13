import os
import time
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT = Path.home() / "storage" / "shared"
DB = Path.home() / "vasuki" / "vasuki.db"

IGNORED_DIRS = {
    ".thumbnails",
    ".cache",
    "cache",
    "tmp",
    "temp",
    "node_modules",
    ".git",
    "__pycache__",
    ".gradle",
    ".npm",
    ".venv",
    "venv",
}

IGNORED_NAMES = {
    ".nomedia",
}

MAX_FILE_SIZE = 50 * 1024 * 1024

SUPPORTED_EXTENSIONS = {
    ".txt", ".md", ".markdown",
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".json", ".yaml", ".yml", ".xml",
    ".csv", ".sql", ".sh", ".bash",
    ".html", ".css",
    ".ini", ".cfg", ".conf",
    ".log",
    ".pdf", ".docx",
}

conn = sqlite3.connect(DB, timeout=30)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS processing_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE,
    status TEXT DEFAULT 'pending',
    updated_at TEXT
)
""")

conn.commit()

# Upgrade an existing queue table without destroying it.
columns = {
    row[1]
    for row in cur.execute("PRAGMA table_info(processing_queue)")
}

if "file_size" not in columns:
    cur.execute("ALTER TABLE processing_queue ADD COLUMN file_size INTEGER")

if "extension" not in columns:
    cur.execute("ALTER TABLE processing_queue ADD COLUMN extension TEXT")

conn.commit()


def should_ignore(path: Path) -> bool:
    try:
        if any(part in IGNORED_DIRS for part in path.parts):
            return True

        if path.name in IGNORED_NAMES:
            return True

        if path.name.startswith(".~"):
            return True

        if path.is_symlink():
            return True

        if not path.is_file():
            return True

        size = path.stat().st_size

        if size > MAX_FILE_SIZE:
            return True

        return False

    except OSError:
        return True


def should_queue(path: Path) -> bool:
    if should_ignore(path):
        return False

    suffix = path.suffix.lower()

    # Keep unknown files out of the processing pipeline for now.
    if suffix not in SUPPORTED_EXTENSIONS:
        return False

    return True


def enqueue_file(path: Path) -> bool:
    if not should_queue(path):
        return False

    try:
        stat = path.stat()

        cur.execute("""
            INSERT OR IGNORE INTO processing_queue
                (path, status, updated_at, file_size, extension)
            VALUES (?, 'pending', ?, ?, ?)
        """, (
            str(path),
            datetime.now().isoformat(),
            stat.st_size,
            path.suffix.lower(),
        ))

        return cur.rowcount > 0

    except (OSError, sqlite3.Error):
        return False


def scan_loop():
    print("QUEUE DAEMON STARTED", flush=True)
    print(f"ROOT: {ROOT}", flush=True)
    print(f"DB: {DB}", flush=True)

    while True:
        try:
            scanned = 0
            queued = 0

            for root, dirs, files in os.walk(ROOT):
                # Prevent traversal into known Android/system noise.
                dirs[:] = [
                    d for d in dirs
                    if d not in IGNORED_DIRS
                ]

                for filename in files:
                    scanned += 1

                    path = Path(root) / filename

                    if enqueue_file(path):
                        queued += 1

            conn.commit()

            print(
                f"SCAN ROUND COMPLETE | scanned={scanned} new={queued}",
                flush=True,
            )

        except Exception as exc:
            print(f"SCAN ERROR: {exc}", flush=True)

            try:
                conn.rollback()
            except sqlite3.Error:
                pass

        time.sleep(30)


if __name__ == "__main__":
    scan_loop()
