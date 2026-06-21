import sqlite3
import time
import json
import hashlib
from datetime import datetime
import difflib
import os

DB_PATH = os.path.expanduser("~/vasuki/vasuki.db")
SNAPSHOT_TABLE = "snapshots"
EVENT_TABLE = "snapshot_events"

# -------------------------
# DB INIT
# -------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(f"""
    CREATE TABLE IF NOT EXISTS {SNAPSHOT_TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        hash TEXT,
        data TEXT
    )
    """)

    cur.execute(f"""
    CREATE TABLE IF NOT EXISTS {EVENT_TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        change_type TEXT,
        detail TEXT
    )
    """)

    conn.commit()
    conn.close()


# -------------------------
# SYSTEM STATE COLLECTOR
# -------------------------
def collect_state():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    state = {}

    tables = cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()

    for (t,) in tables:
        try:
            count = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            state[t] = count
        except:
            state[t] = "ERR"

    conn.close()
    return state


# -------------------------
# HASH ENGINE
# -------------------------
def state_hash(state):
    raw = json.dumps(state, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


# -------------------------
# SAVE SNAPSHOT
# -------------------------
def save_snapshot(state, h):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        f"INSERT INTO {SNAPSHOT_TABLE} (timestamp, hash, data) VALUES (?, ?, ?)",
        (datetime.utcnow().isoformat(), h, json.dumps(state))
    )

    conn.commit()
    conn.close()


# -------------------------
# LOAD LAST SNAPSHOT
# -------------------------
def load_last_snapshot():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    row = cur.execute(
        f"SELECT data FROM {SNAPSHOT_TABLE} ORDER BY id DESC LIMIT 1"
    ).fetchone()

    conn.close()

    if row:
        return json.loads(row[0])
    return None


# -------------------------
# DIFF ENGINE
# -------------------------
def diff_states(old, new):
    changes = []

    all_keys = set(old.keys()).union(set(new.keys()))

    for k in all_keys:
        if k not in old:
            changes.append(("NEW_TABLE", k, new[k]))
        elif k not in new:
            changes.append(("REMOVED_TABLE", k, old[k]))
        elif old[k] != new[k]:
            changes.append(("CHANGE", k, f"{old[k]} -> {new[k]}"))

    return changes


# -------------------------
# EVENT LOGGER
# -------------------------
def log_event(change_type, detail):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        f"INSERT INTO {EVENT_TABLE} (timestamp, change_type, detail) VALUES (?, ?, ?)",
        (datetime.utcnow().isoformat(), change_type, str(detail))
    )

    conn.commit()
    conn.close()


# -------------------------
# CORE LOOP
# -------------------------

def analyze_drift_history():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    rows = cur.execute(f"""
        SELECT change_type, detail
        FROM {EVENT_TABLE}
        ORDER BY id DESC
        LIMIT 50
    """).fetchall()

    conn.close()

    pattern_score = {}

    for r in rows:
        key = r[0]
        pattern_score[key] = pattern_score.get(key, 0) + 1

    return pattern_score

def run_cycle():
    state = collect_state()
    h = state_hash(state)

    last = load_last_snapshot()

    print("\n========================")
    print("VASUKI SNAPSHOT CYCLE")
    print("========================")
    print("TIME:", datetime.utcnow().isoformat())
    print("HASH:", h)

    if last:
        changes = diff_states(last, state)

        if not changes:
            print("STATUS: NO DRIFT DETECTED")
            log_event("NO_DRIFT", "stable_state")

        else:
            print("STATUS: DRIFT DETECTED")

            for c in changes:
                print(" -", c)
                log_event(c[0], c)

    else:
        print("STATUS: INITIAL SNAPSHOT")
        log_event("INIT", "first_snapshot")

    save_snapshot(state, h)


# -------------------------
# MAIN LOOP
# -------------------------
if __name__ == "__main__":
    init_db()

    while True:
        run_cycle()
        time.sleep(10)
