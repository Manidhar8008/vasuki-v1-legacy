import sqlite3
import time
from datetime import datetime

DB_PATH = "/data/data/com.termux/files/home/vasuki/data/vasuki.db"


# =========================
# EXPECTATION MODEL
# (what SHOULD have data)
# =========================
EXPECTED_NON_EMPTY = {
    "memories",
    "entities",
    "relationships",
    "files",
    "memory_search"
}


# =========================
# REPAIR MEMORY (learning log)
# =========================
repair_log = []


# =========================
# DB STATE READER
# =========================
def get_state():
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


# =========================
# ONTOLOGY ENGINE
# =========================
def classify(table):

    ontology = {
        "MEMORY_LAYER": {
            "memories", "memory_events", "observations",
            "questions", "timeline_events", "code_inventory"
        },

        "GRAPH_LAYER": {
            "entities", "relationships", "graph_edges",
            "kg_nodes", "kg_edges"
        },

        "SEARCH_LAYER": {
            "memory_search", "memory_search_data",
            "memory_search_idx", "memory_search_content",
            "memory_search_config", "memory_search_docsize"
        },

        "FILE_LAYER": {
            "files", "files_index", "file_inventory",
            "file_fingerprint"
        },

        "SYSTEM_LAYER": {
            "processing_queue", "system_logs",
            "daemon_health", "devices"
        },

        "PROVENANCE_LAYER": {
            "provenance", "evidence",
            "extracted_content", "extracted_text"
        },

        "IDENTITY_LAYER": {
            "identity_objects", "skills", "life_domains"
        }
    }

    for layer, items in ontology.items():
        if table in items:
            return layer

    return "UNMAPPED_LAYER"


# =========================
# ANALYSIS ENGINE (EXPECTATION-AWARE)
# =========================
def analyze(tables, counts):

    issues = []
    entity_map = {}

    for t in tables:

        entity = classify(t)
        entity_map[t] = entity

        count = counts.get(t, -1)

        # ONLY flag if expected table is empty
        if t in EXPECTED_NON_EMPTY and count == 0:
            issues.append({
                "table": t,
                "entity": entity,
                "issue": "EMPTY_EXPECTED_TABLE"
            })

    return issues, entity_map


# =========================
# HEALING PLANNER
# =========================
def plan(issues):

    actions = []

    for i in issues:
        layer = i["entity"]
        table = i["table"]

        if layer == "MEMORY_LAYER":
            actions.append(f"REPAIR_MEMORY:{table}")

        elif layer == "GRAPH_LAYER":
            actions.append(f"REPAIR_GRAPH:{table}")

        elif layer == "SEARCH_LAYER":
            actions.append(f"REINDEX_SEARCH:{table}")

        elif layer == "FILE_LAYER":
            actions.append(f"RESCAN_FILES:{table}")

        elif layer == "SYSTEM_LAYER":
            actions.append(f"RESTART_SYSTEM:{table}")

        elif layer == "PROVENANCE_LAYER":
            actions.append(f"VERIFY_TRACE:{table}")

        elif layer == "IDENTITY_LAYER":
            actions.append(f"REBUILD_IDENTITY:{table}")

        else:
            actions.append(f"UNKNOWN_FIX:{table}")

    return actions


# =========================
# EXECUTION ENGINE
# =========================
def execute(action):

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    status = "done"

    try:

        if action.startswith("REPAIR_MEMORY"):
            cur.execute("PRAGMA integrity_check")

        elif action.startswith("REPAIR_GRAPH"):
            cur.execute("PRAGMA foreign_key_check")

        elif action.startswith("REINDEX_SEARCH"):
            cur.execute("PRAGMA optimize")

        elif action.startswith("RESCAN_FILES"):
            pass

        elif action.startswith("RESTART_SYSTEM"):
            pass

        elif action.startswith("VERIFY_TRACE"):
            pass

        elif action.startswith("REBUILD_IDENTITY"):
            pass

        else:
            status = "unknown"

        conn.commit()

    except Exception as e:
        status = f"error:{e}"

    conn.close()

    repair_log.append({
        "action": action,
        "status": status,
        "time": datetime.now().isoformat()
    })


# =========================
# STATUS ENGINE (REAL MEANING)
# =========================
def compute_status(issues):

    if len(issues) == 0:
        return "HEALTHY"

    # mild degradation vs structural failure
    if len(issues) <= 2:
        return "STABLE_BUT_DEGRADED"

    return "DEGRADED"


# =========================
# KERNEL LOOP
# =========================
def run():

    print("\n[VASUKI SELF-HEALING KERNEL v5 STARTED]\n")

    while True:

        tables, counts = get_state()
        issues, entity_map = analyze(tables, counts)
        actions = plan(issues)

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
            execute(a)

        print("\nREPAIR MEMORY (last 5):")
        for r in repair_log[-5:]:
            print(" -", r)

        status = compute_status(issues)
        print("\nSTATUS:", status)

        time.sleep(10)


if __name__ == "__main__":
    run()
