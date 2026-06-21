import sqlite3
import re
from pathlib import Path
from datetime import datetime

DB = Path.home() / "vasuki" / "data" / "vasuki.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("""
DELETE FROM observations
""")

conn.commit()

rules = [

    ("employment",
     r"cognizant|genpact|offer letter|appointment letter|employee"),

    ("education",
     r"university|college|degree|certificate|course"),

    ("analytics",
     r"business analyst|power bi|sql|tableau|analytics"),

    ("machine_learning",
     r"machine learning|python|artificial intelligence|ai"),

    ("salary",
     r"salary|payslip|pay slip|ctc"),

    ("government",
     r"passport|aadhaar|pan card"),

    ("banking",
     r"account statement|bank statement")
]

cur.execute("""
SELECT file_path, content
FROM extracted_text
""")

rows = cur.fetchall()

added = 0

for file_path, content in rows:

    if not content:
        continue

    text = content.lower()

    for obs_type, pattern in rules:

        if re.search(pattern, text):

            observation = f"{obs_type} evidence detected"

            cur.execute("""
            INSERT INTO observations(
                source_path,
                observation_type,
                confidence,
                observation,
                created_at
            )
            VALUES(?,?,?,?,?)
            """, (
                file_path,
                obs_type,
                0.90,
                observation,
                datetime.now().isoformat()
            ))

            added += 1

conn.commit()

print()
print("OBSERVATIONS CREATED:", added)
print()

conn.close()
