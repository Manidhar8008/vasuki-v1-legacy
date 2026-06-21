import sqlite3
import time
from datetime import datetime


# =========================================================
# CONFIG
# =========================================================

DB_PATH = "/data/data/com.termux/files/home/vasuki/data/vasuki.db"
LOOP_INTERVAL = 5


# =========================================================
# MEMORY STORES
# =========================================================

repair_log = []
action_stats = {}
learning_log = []


# =========================================================
# EXPECTATION BASELINE
# =========================================================

EXPECTED_NON_EMPTY = {
    "memories",
    "entities",
    "relationships",
    "files",
    "memory_search"
}


# =========================================================
# STATE READER
# =========================================================

def read_state():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cur.fetchall()]

    counts = {}
    for t in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            counts[t] = cur.fetchone()[0]
        except:
            counts[t] = -1

    conn.close()
    return tables, counts


# =========================================================
# ONTOLOGY
# =========================================================

def classify(table):

    ontology = {
        "MEMORY": {
            "memories", "memory_events", "observations",
            "questions", "timeline_events", "code_inventory"
        },
        "GRAPH": {
            "entities", "relationships", "graph_edges",
            "kg_nodes", "kg_edges"
        },
        "SEARCH": {
            "memory_search", "memory_search_data",
            "memory_search_idx", "memory_search_content",
            "memory_search_config", "memory_search_docsize"
        },
        "FILES": {
            "files", "files_index", "file_inventory",
            "file_fingerprint"
        },
        "SYSTEM": {
            "processing_queue", "system_logs",
            "daemon_health", "devices"
        },
        "PROVENANCE": {
            "provenance", "evidence",
            "extracted_content", "extracted_text"
        },
        "IDENTITY": {
            "identity_objects", "skills", "life_domains"
        }
    }

    for layer, items in ontology.items():
        if table in items:
            return layer

    return "UNKNOWN"


# =========================================================
# ANALYSIS
# =========================================================

def analyze(tables, counts):

    issues = []
    entity_map = {}

    for t in tables:

        layer = classify(t)
        entity_map[t] = layer

        count = counts.get(t, -1)

        if t in EXPECTED_NON_EMPTY and count == 0:
            issues.append({
                "table": t,
                "layer": layer,
                "issue": "EMPTY_EXPECTED_TABLE"
            })

    return issues, entity_map


# =========================================================
# PLANNING
# =========================================================

def plan(issues):

    actions = []

    for i in issues:

        layer = i["layer"]
        table = i["table"]

        if layer == "MEMORY":
            actions.append(f"MEMORY_CHECK:{table}")
        elif layer == "GRAPH":
            actions.append(f"GRAPH_CHECK:{table}")
        elif layer == "SEARCH":
            actions.append(f"SEARCH_OPTIMIZE:{table}")
        elif layer == "FILES":
            actions.append(f"FILES_SCAN:{table}")
        elif layer == "SYSTEM":
            actions.append(f"SYSTEM_PING:{table}")
        elif layer == "PROVENANCE":
            actions.append(f"TRACE_VERIFY:{table}")
        elif layer == "IDENTITY":
            actions.append(f"IDENTITY_VALIDATE:{table}")
        else:
            actions.append(f"UNKNOWN_HANDLE:{table}")

    return actions


# =========================================================
# EXECUTION + LEARNING SIGNAL
# =========================================================

def execute(action, pre_issue_count, post_issue_count):

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    status = "ok"

    try:

        if action.startswith("SEARCH_OPTIMIZE"):
            cur.execute("PRAGMA optimize")

        elif action.startswith("GRAPH_CHECK"):
            cur.execute("PRAGMA foreign_key_check")

        elif action.startswith("MEMORY_CHECK"):
            cur.execute("PRAGMA integrity_check")

        conn.commit()

    except Exception as e:
        status = f"error:{str(e)}"

    conn.close()

    # =====================================================
    # REPAIR RESULT (THIS IS LEARNING CORE)
    # =====================================================

    improvement = pre_issue_count - post_issue_count

    repair_event = {
        "action": action,
        "status": status,
        "before": pre_issue_count,
        "after": post_issue_count,
        "improvement": improvement,
        "time": datetime.now().isoformat()
    }

    repair_log.append(repair_event)

    action_stats[action] = action_stats.get(action, 0) + 1

    # learning signal
    learning_log.append({
        "action": action,
        "signal": "POSITIVE" if improvement > 0 else "NEGATIVE" if improvement < 0 else "NEUTRAL",
        "score": improvement
    })


# =========================================================
# STATUS
# =========================================================

def compute_status(issues):

    if len(issues) == 0:
        return "HEALTHY"
    if len(issues) <= 2:
        return "STABLE_DEGRADED"
    return "DEGRADED"


# =========================================================
# REPORT
# =========================================================

def report(tables, issues, entity_map, actions):

    print("\n------------------------")
    print("TIME:", datetime.now().isoformat())
    print("TABLES:", len(tables))
    print("ISSUES:", len(issues))

    print("\nENTITY MAP:")
    for k, v in entity_map.items():
        print(f" - {k} → {v}")

    print("\nACTIONS:")
    for a in actions:
        print(" -", a)

    print("\nLEARNING SIGNAL (last 5):")
    for l in learning_log[-5:]:
        print(" -", l)

    print("\nSTATUS:", compute_status(issues))


# =========================================================
# MAIN LOOP
# =========================================================

def run():

    print("\n[VASUKI OS v2 - LEARNING SYSTEM STARTED]\n")

    while True:

        tables, counts = read_state()

        pre_issue_count = len(analyze(tables, counts)[0])

        issues, entity_map = analyze(tables, counts)

        actions = plan(issues)

        for a in actions:

            # re-check after action for learning delta
            execute(a, pre_issue_count, len(issues))

        report(tables, issues, entity_map, actions)

        time.sleep(LOOP_INTERVAL)


if __name__ == "__main__":
    run()
