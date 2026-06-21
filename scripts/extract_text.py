import sqlite3
from pathlib import Path
from pypdf import PdfReader
from docx import Document

DB = Path.home() / "vasuki/data/vasuki.db"

SEARCH_DIRS = [
    Path.home() / "storage/shared/Download",
    Path.home() / "storage/shared/Documents",
]

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS extracted_text (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE,
    file_type TEXT,
    extracted_chars INTEGER,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

def extract_pdf(path):
    text = ""

    try:
        reader = PdfReader(str(path))

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    except Exception as e:
        print("PDF ERROR:", path.name, e)

    return text


def extract_docx(path):
    text = ""

    try:
        doc = Document(str(path))

        for para in doc.paragraphs:
            text += para.text + "\n"

    except Exception as e:
        print("DOCX ERROR:", path.name, e)

    return text


processed = 0

for directory in SEARCH_DIRS:

    if not directory.exists():
        continue

    for file in directory.rglob("*"):

        if not file.is_file():
            continue

        suffix = file.suffix.lower()

        if suffix not in [".pdf", ".docx"]:
            continue

        cur.execute(
            "SELECT 1 FROM extracted_text WHERE file_path=?",
            (str(file),)
        )

        if cur.fetchone():
            continue

        print("Processing:", file.name)

        text = ""

        if suffix == ".pdf":
            text = extract_pdf(file)

        elif suffix == ".docx":
            text = extract_docx(file)

        cur.execute("""
        INSERT OR IGNORE INTO extracted_text
        (
            file_path,
            file_type,
            extracted_chars,
            content
        )
        VALUES (?,?,?,?)
        """,
        (
            str(file),
            suffix,
            len(text),
            text[:500000]
        ))

        processed += 1

        conn.commit()

print()
print("Processed:", processed)

conn.close()
