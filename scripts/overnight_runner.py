import time
import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path.home() / "vasuki" / "data" / "vasuki.db"
LOG = Path.home() / "vasuki" / "vasuki_overnight.log"

def log(msg):
    with open(LOG, "a") as f:
        f.write(f"{datetime.now().isoformat()} | {msg}\n")

def checkpoint(cur):
    cur.execute("SELECT COUNT(*) FROM processing_queue WHERE status='pending'")
    pending = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM memories")
    mem = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM provenance")
    prov = cur.fetchone()[0]

    log(f"CHECKPOINT | pending={pending} memories={mem} provenance={prov}")

def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    log("OVERNIGHT RUN STARTED")

    while True:
        try:
            # 1. slow drain (safe batch processing)
            cur.execute("""
                UPDATE processing_queue
                SET status='processing'
                WHERE id IN (
                    SELECT id FROM processing_queue
                    WHERE status='pending'
                    LIMIT 20
                )
            """)
            conn.commit()

            # 2. checkpoint system state
            checkpoint(cur)

            # 3. sleep (prevents locks + CPU spike)
            time.sleep(30)

        except Exception as e:
            log(f"ERROR: {str(e)}")
            time.sleep(60)

if __name__ == "__main__":
    main()
