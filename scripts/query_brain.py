import sqlite3
from pathlib import Path

DB = Path.home() / "vasuki" / "data" / "vasuki.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

def run(query):
    cur.execute(query)
    rows = cur.fetchall()
    for r in rows:
        print(r)

print("\nVASUKI QUERY BRAIN READY\n")

print("MEMORIES:")
run("SELECT memory_type, COUNT(*) FROM memories GROUP BY memory_type")

print("\nOBSERVATIONS:")
run("SELECT observation_type, COUNT(*) FROM observations GROUP BY observation_type")

print("\nSKILLS:")
run("SELECT skill_name, confidence FROM skills ORDER BY confidence DESC")

print("\nPROVENANCE SAMPLE:")
run("SELECT source_file, COUNT(*) FROM provenance GROUP BY source_file LIMIT 10")

print("\nTIMELINE:")
run("SELECT event_type, COUNT(*) FROM timeline_events GROUP BY event_type")
