import sqlite3
import re
from pathlib import Path

DB = Path.home() / "vasuki" / "data" / "vasuki.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Load extracted docs
cur.execute("SELECT file_path, content FROM extracted_text")
rows = cur.fetchall()

def extract_keywords(text):
    text = text.lower()

    # very simple heuristic extractor (fast + offline)
    keywords = set()

    patterns = [
        r"\bsql\b",
        r"\bpython\b",
        r"\bpower bi\b",
        r"\btableau\b",
        r"\bexcel\b",
        r"\baws\b",
        r"\bazure\b",
        r"\bdevops\b",
        r"\bdata analysis\b",
        r"\bmachine learning\b",
        r"\bapi\b",
        r"\bjson\b",
        r"\breact\b",
        r"\bsap\b"
    ]

    for p in patterns:
        if re.search(p, text):
            keywords.add(p.replace("\\b", "").strip())

    return list(keywords)

def add_node(node_type, value):
    cur.execute("""
    INSERT OR IGNORE INTO kg_nodes(node_type, value)
    VALUES (?, ?)
    """, (node_type, value))

def add_edge(src, relation, dst, file):
    cur.execute("""
    INSERT INTO kg_edges(src, relation, dst, source_file)
    VALUES (?, ?, ?, ?)
    """, (src, relation, dst, file))

count = 0

for file_path, content in rows:
    if not content:
        continue

    doc_node = file_path.split("/")[-1]

    add_node("document", doc_node)

    keywords = extract_keywords(content)

    for kw in keywords:
        add_node("entity", kw)

        add_edge(doc_node, "mentions", kw, file_path)

    count += 1

    if count % 20 == 0:
        conn.commit()
        print(f"Processed {count} documents")

conn.commit()

print("DONE KG BUILD")
conn.close()
