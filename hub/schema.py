"""Vasuki Hub - versioned schema for the unified powerhouse database.

One database. Immutable event timeline at the core; knowledge graph,
documents, telemetry, projects and projections derived from it.
Schema evolves forward through integer-versioned migrations.
"""

APPLICATION_ID = 0x56415355  # 'VASU'
CURRENT_VERSION = 1

# Bootstrap table that tracks applied migrations. Created by the runner,
# not part of any migration.
BOOTSTRAP = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version    INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    applied_at TEXT NOT NULL
);
"""

MIGRATIONS = [
    {
        "version": 1,
        "name": "init_unified_hub",
        "sql": """
-- =====================================================================
-- CORE: immutable timeline (the atomic record of everything that happens)
-- =====================================================================
CREATE TABLE timeline (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts         TEXT NOT NULL,            -- ISO-8601 UTC (human readable)
    ts_micros  INTEGER NOT NULL,         -- monotonic order key (us)
    source     TEXT NOT NULL,            -- vasuki_os | sense | ask | hub | app.<name>
    domain     TEXT NOT NULL,            -- system|knowledge|sensor|identity|projects|life|health
    etype      TEXT NOT NULL,            -- created|updated|ingested|observed|drift|query|decided|error|boot ...
    key        TEXT,                     -- subject UID / key (file path, entity uid, sensor id, app id)
    payload    TEXT NOT NULL DEFAULT '{}', -- JSON object (free-form, versioned inside)
    idem_key   TEXT UNIQUE               -- sha256 idempotency key (duplicates ignored)
);
CREATE INDEX idx_timeline_ts     ON timeline(ts_micros DESC, id);
CREATE INDEX idx_timeline_domain ON timeline(domain, ts_micros DESC);
CREATE INDEX idx_timeline_source ON timeline(source, ts_micros DESC);
CREATE INDEX idx_timeline_key    ON timeline(key, ts_micros DESC);

-- =====================================================================
-- KNOWLEDGE GRAPH: entities (nodes) + relationships (typed edges)
-- =====================================================================
CREATE TABLE entities (
    uid        TEXT PRIMARY KEY,
    kind       TEXT NOT NULL,            -- person|place|document|project|app|sensor|device|concept|agent|life|health
    name       TEXT NOT NULL,
    summary    TEXT,
    attrs      TEXT NOT NULL DEFAULT '{}', -- JSON (arbitrary per-kind metadata)
    embedding  BLOB,                       -- optional float32 vector
    created_ts TEXT NOT NULL,
    updated_ts TEXT NOT NULL
);
CREATE INDEX idx_entities_kind ON entities(kind);
CREATE INDEX idx_entities_name ON entities(name);

CREATE TABLE relationships (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    src        TEXT NOT NULL REFERENCES entities(uid) ON DELETE CASCADE,
    rel        TEXT NOT NULL,              -- authored_by|part_of|depends_on|knows|located_at|tracks|derived_from
    dst        TEXT NOT NULL REFERENCES entities(uid) ON DELETE CASCADE,
    attrs      TEXT NOT NULL DEFAULT '{}',
    valid_from TEXT,
    valid_to   TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX idx_rel_src ON relationships(src);
CREATE INDEX idx_rel_dst ON relationships(dst);

-- =====================================================================
-- KNOWLEDGE LAYER: documents -> chunks, chunk text in FTS5, vector in BLOB
-- =====================================================================
CREATE TABLE documents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    uid         TEXT UNIQUE,              -- links to entities.uid
    path        TEXT UNIQUE,
    hash        TEXT NOT NULL,
    size_bytes  INTEGER,
    mime        TEXT,
    domain      TEXT DEFAULT 'personal',  -- personal|source|work
    attrs       TEXT DEFAULT '{}',
    imported_at TEXT NOT NULL
);
CREATE INDEX idx_documents_domain ON documents(domain);

CREATE TABLE knowledge_chunks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id     INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    idx        INTEGER NOT NULL,
    text       TEXT NOT NULL,
    char_count INTEGER,
    embedding  BLOB,                    -- float32 vector
    hash       TEXT NOT NULL UNIQUE      -- sha256 of text (dedupe across re-ingests)
);
CREATE INDEX idx_kc_doc ON knowledge_chunks(doc_id);

CREATE VIRTUAL TABLE knowledge_fts USING fts5(
    text,
    content='knowledge_chunks',
    content_rowid='id'
);
CREATE TRIGGER knowledge_chunks_ai AFTER INSERT ON knowledge_chunks BEGIN
    INSERT INTO knowledge_fts(rowid, text) VALUES (new.id, new.text);
END;
CREATE TRIGGER knowledge_chunks_ad AFTER DELETE ON knowledge_chunks BEGIN
    INSERT INTO knowledge_fts(knowledge_fts, rowid, text) VALUES('delete', old.id, old.text);
END;
CREATE TRIGGER knowledge_chunks_au AFTER UPDATE ON knowledge_chunks BEGIN
    INSERT INTO knowledge_fts(knowledge_fts, rowid, text) VALUES('delete', old.id, old.text);
    INSERT INTO knowledge_fts(rowid, text) VALUES (new.id, new.text);
END;

-- =====================================================================
-- SENSOR / TELEMETRY: numeric time series (bucketed, compact)
-- =====================================================================
CREATE TABLE telemetry (
    bucket  INTEGER NOT NULL,           -- epoch seconds, 1h bucket
    sensor  TEXT NOT NULL,
    metric  TEXT NOT NULL,
    count   INTEGER NOT NULL DEFAULT 0,
    sum     REAL NOT NULL DEFAULT 0,
    min     REAL,
    max     REAL,
    attrs   TEXT DEFAULT '{}',
    PRIMARY KEY (bucket, sensor, metric)
);
CREATE INDEX idx_tel_sensor ON telemetry(sensor, bucket);

-- =====================================================================
-- PROJECTS & PROGRAMMES: every app/agent you build is a first-class citizen
-- =====================================================================
CREATE TABLE apps (
    app_id     TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    kind       TEXT NOT NULL,            -- programme|agent|routine|library
    status     TEXT NOT NULL DEFAULT 'active',
    version    TEXT NOT NULL DEFAULT '0.0.1',
    manifest   TEXT DEFAULT '{}',        -- capabilities / entrypoints
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- =====================================================================
-- PROJECTIONS: materialized derived state over the timeline
-- =====================================================================
CREATE TABLE projections (
    name TEXT NOT NULL,
    ts   TEXT NOT NULL,
    hash TEXT,
    data TEXT NOT NULL,                  -- JSON
    PRIMARY KEY (name, ts)
);
"""
    },
]


def ensure_application_id(conn):
    conn.execute(f"PRAGMA application_id = {APPLICATION_ID}")


def apply_migrations(conn, now=None):
    """Create the migration ledger and apply every pending migration.

    Returns the list of (version, name) applied in this call.
    """
    from datetime import datetime, timezone

    ensure_iso = now or (lambda: datetime.now(timezone.utc).isoformat())
    conn.execute(BOOTSTRAP)
    conn.commit()

    applied = {
        r[0] for r in conn.execute("SELECT version FROM schema_migrations").fetchall()
    }

    done = []
    for mig in sorted(MIGRATIONS, key=lambda m: m["version"]):
        if mig["version"] in applied:
            continue
        conn.execute("BEGIN")
        try:
            conn.executescript(mig["sql"])
            conn.execute(
                "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
                (mig["version"], mig["name"], ensure_iso()),
            )
            conn.execute(
                f"PRAGMA user_version = {mig['version']};"
            )
            conn.commit()
            done.append(mig["version"])
        except Exception:
            conn.rollback()
            raise

    return done