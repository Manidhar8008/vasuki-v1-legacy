import sqlite3
from pypdf import PdfReader

DB = "/data/data/com.termux/files/home/vasuki/data/vasuki.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("""
SELECT id, filename, path, ai_category, importance
FROM files
WHERE extension='.pdf'
""")

files = cur.fetchall()

for file_id, filename, path, category, importance in files:

    try:
        pdf = PdfReader(path)

        text = ""

        for page in pdf.pages[:3]:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        if len(text.strip()) < 20:
            continue

        summary = text[:1000]

        keywords = ",".join(
            list(
                set(
                    w.lower()
                    for w in text.split()
                    if len(w) > 5
                )
            )[:20]
        )

        cur.execute("""
        INSERT INTO memories
        (
            source_file,
            source_path,
            memory_type,
            summary,
            keywords,
            importance
        )
        VALUES (?,?,?,?,?,?)
        """,
        (
            file_id,
            path,
            category or "pdf",
            summary,
            keywords,
            importance or 1
        ))

        print("Indexed:", filename)

    except Exception as e:
        print("Failed:", filename, e)

conn.commit()
conn.close()

print("\nDone.")
