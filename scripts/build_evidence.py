import sqlite3
from pathlib import Path

DB = Path.home() / "vasuki" / "data" / "vasuki.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS evidence(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT,
    filename TEXT,
    evidence_type TEXT,
    confidence INTEGER DEFAULT 1
)
""")

KEYWORDS = {
    "resume":"career",
    "cv":"career",
    "offer":"job",
    "joining":"job",
    "appointment":"job",
    "certificate":"education",
    "degree":"education",
    "internship":"career",
    "salary":"finance",
    "payslip":"finance",
    "cognizant":"career",
    "genpact":"career",
    "lunar":"career",
    "business analyst":"career"
}

cur.execute("""
SELECT path,filename
FROM file_inventory
""")

rows = cur.fetchall()

count = 0

for path, filename in rows:

    name = str(filename).lower()

    for keyword, category in KEYWORDS.items():

        if keyword in name:

            cur.execute("""
            INSERT INTO evidence(
                path,
                filename,
                evidence_type
            )
            VALUES(?,?,?)
            """,(path,filename,category))

            count += 1
            break

conn.commit()

print("Evidence Found:", count)

conn.close()
