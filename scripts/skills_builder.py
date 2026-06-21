import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path.home() / "vasuki" / "data" / "vasuki.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

SKILLS = {
    "Business Analysis": [
        "business analyst",
        "requirement gathering",
        "stakeholder",
        "brd",
        "frd",
        "user story"
    ],
    "SQL": [
        "sql",
        "oracle",
        "mysql",
        "query"
    ],
    "Power BI": [
        "power bi",
        "dashboard",
        "dax"
    ],
    "Excel": [
        "excel",
        "pivot table",
        "vlookup",
        "spreadsheet"
    ],
    "Python": [
        "python",
        "pandas",
        "numpy"
    ],
    "Agile": [
        "agile",
        "scrum",
        "sprint"
    ],
    "Collections": [
        "collections",
        "o2c",
        "order to cash",
        "accounts receivable"
    ],
    "Data Analysis": [
        "analytics",
        "analysis",
        "data analyst"
    ],
    "Machine Learning": [
        "machine learning",
        "ml",
        "artificial intelligence"
    ]
}

cur.execute("""
SELECT content
FROM extracted_text
""")

rows = cur.fetchall()

results = {}

for (content,) in rows:

    if not content:
        continue

    text = content.lower()

    for skill, keywords in SKILLS.items():

        hits = 0

        for keyword in keywords:
            if keyword in text:
                hits += 1

        if hits > 0:

            if skill not in results:
                results[skill] = 0

            results[skill] += hits

cur.execute("DELETE FROM skills")

for skill, score in results.items():

    confidence = min(score / 10.0, 1.0)

    cur.execute("""
    INSERT INTO skills(
        skill_name,
        confidence,
        evidence_count,
        last_updated
    )
    VALUES (?, ?, ?, ?)
    """, (
        skill,
        confidence,
        score,
        datetime.now().isoformat()
    ))

conn.commit()

print("Skills discovered:", len(results))

conn.close()
