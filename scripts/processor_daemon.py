import sqlite3
import time
from pathlib import Path
from datetime import datetime

DB = Path.home() / "vasuki" / "vasuki.db"

TEXT_EXTENSIONS = {
    ".txt", ".md", ".markdown",
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".json", ".yaml", ".yml", ".xml",
    ".csv", ".sql", ".sh", ".bash",
    ".html", ".css",
    ".ini", ".cfg", ".conf",
    ".log",
}


def connect():
    return sqlite3.connect(DB, timeout=30)


def initialize_database(conn):
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS processing_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE,
            status TEXT DEFAULT 'pending',
            updated_at TEXT
        )
    """)

    columns = {
        row[1]
        for row in cur.execute("PRAGMA table_info(processing_queue)")
    }

    if "file_size" not in columns:
        cur.execute(
            "ALTER TABLE processing_queue ADD COLUMN file_size INTEGER"
        )

    if "extension" not in columns:
        cur.execute(
            "ALTER TABLE processing_queue ADD COLUMN extension TEXT"
        )

    cur.execute("""
        CREATE TABLE IF NOT EXISTS extracted_text (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE,
            file_type TEXT,
            extracted_chars INTEGER,
            content TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()


def fetch_batch(conn, limit=10):
    cur = conn.cursor()

    cur.execute("""
        SELECT id, path
        FROM processing_queue
        WHERE status='pending'
        ORDER BY id
        LIMIT ?
    """, (limit,))

    return cur.fetchall()


def update_status(conn, item_id, status):
    conn.execute("""
        UPDATE processing_queue
        SET status=?, updated_at=?
        WHERE id=?
    """, (
        status,
        datetime.now().isoformat(),
        item_id,
    ))

    conn.commit()


def read_text_file(path: Path):
    encodings = (
        "utf-8",
        "utf-8-sig",
        "utf-16",
        "latin-1",
    )

    for encoding in encodings:
        try:
            return path.read_text(
                encoding=encoding,
                errors="replace",
            )
        except Exception:
            continue

    return ""


def extract_pdf(path: Path):
    try:
        from pypdf import PdfReader
    except ImportError:
        return None

    try:
        reader = PdfReader(str(path))
        chunks = []

        for page in reader.pages:
            text = page.extract_text()
            if text:
                chunks.append(text)

        return "\n".join(chunks)

    except Exception as exc:
        raise RuntimeError(f"PDF extraction failed: {exc}") from exc


def extract_docx(path: Path):
    try:
        from docx import Document
    except ImportError:
        return None

    try:
        document = Document(str(path))
        return "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )

    except Exception as exc:
        raise RuntimeError(f"DOCX extraction failed: {exc}") from exc


def extract_content(path: Path):
    suffix = path.suffix.lower()

    if suffix in TEXT_EXTENSIONS:
        return read_text_file(path)

    if suffix == ".pdf":
        return extract_pdf(path)

    if suffix == ".docx":
        return extract_docx(path)

    return None


def store_extracted_text(conn, path: Path, content: str):
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO extracted_text (
            file_path,
            file_type,
            extracted_chars,
            content
        )
        VALUES (?, ?, ?, ?)
        ON CONFLICT(file_path)
        DO UPDATE SET
            file_type=excluded.file_type,
            extracted_chars=excluded.extracted_chars,
            content=excluded.content
    """, (
        str(path),
        path.suffix.lower(),
        len(content or ""),
        (content or "")[:500000],
    ))

    conn.commit()


def process_file(conn, item_id, raw_path):
    path = Path(raw_path)

    print(f"PROCESS: {path}", flush=True)

    if not path.exists():
        update_status(conn, item_id, "missing")
        return

    if not path.is_file():
        update_status(conn, item_id, "ignored")
        return

    update_status(conn, item_id, "processing")

    try:
        content = extract_content(path)

        if content is None:
            update_status(conn, item_id, "ignored")
            print(
                f"IGNORED: no extractor for {path.suffix.lower()}",
                flush=True,
            )
            return

        store_extracted_text(
            conn,
            path,
            content,
        )

        update_status(conn, item_id, "done")

        print(
            f"DONE: {path.name} chars={len(content)}",
            flush=True,
        )

    except Exception as exc:
        print(
            f"FILE ERROR: {path} | {exc}",
            flush=True,
        )

        try:
            update_status(conn, item_id, "error")
        except Exception:
            pass


def loop():
    print("PROCESSOR DAEMON STARTED", flush=True)
    print(f"DB: {DB}", flush=True)

    while True:
        conn = None

        try:
            conn = connect()
            initialize_database(conn)

            rows = fetch_batch(conn)

            if not rows:
                conn.close()
                time.sleep(2)
                continue

            for item_id, path in rows:
                process_file(
                    conn,
                    item_id,
                    path,
                )

            conn.close()

        except Exception as exc:
            print(
                f"LOOP ERROR: {exc}",
                flush=True,
            )

            if conn:
                try:
                    conn.rollback()
                    conn.close()
                except Exception:
                    pass

            time.sleep(3)


if __name__ == "__main__":
    loop()
