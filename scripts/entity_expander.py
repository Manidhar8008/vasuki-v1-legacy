import sqlite3
import re

DB="data/vasuki.db"

conn=sqlite3.connect(DB)
cur=conn.cursor()

SKILLS = [
    "SQL",
    "Python",
    "Excel",
    "Power BI",
    "Tableau",
    "Machine Learning",
    "Azure",
    "AWS",
    "Agile",
    "Data Analysis",
    "Business Analysis",
    "DevOps",
    "SAP"
]

rows = cur.execute("""
SELECT id,summary,keywords
FROM memories
""").fetchall()

added=0

for mem_id,summary,keywords in rows:

    text=f"{summary} {keywords}".lower()

    for skill in SKILLS:

        if skill.lower() in text:

            cur.execute("""
            INSERT OR IGNORE INTO entities(
                entity_name,
                entity_type,
                source_memory,
                confidence
            )
            VALUES(?,?,?,?)
            """,(skill,"skill",mem_id,0.90))

            added+=1

conn.commit()

print("ADDED:",added)

conn.close()
