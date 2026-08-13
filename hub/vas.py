"""Vasuki Hub - stable client API. One database, thousands of programmes."""

import hashlib
import json
import os
import sqlite3
import time

import hub.schema as schema
import hub.semantics as sem
from hub.pipe import HubPipe

DEFAULT_DB = "~/vasuki/hub/vasub.db"
DEFAULT_SIGNAL = "~/vasuki/room_signal.log"


def _connect(db_path):
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.row_factory = sqlite3.Row
    return conn


def _decode_text(raw):
    for enc in ("utf-8", "utf-16-le", "latin-1"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, ValueError):
            continue
    return raw.decode("utf-8", "replace")


class Vas:
    """The unified powerhouse client.

    write path : publish() -> non-blocking pipe -> timeline + room_signal.log
    read path  : synchronous queries against the same store.
    """

    def __init__(self, db_path=None, signal_path=None):
        self.db_path = os.path.expanduser(db_path or DEFAULT_DB)
        self.signal_path = os.path.expanduser(signal_path or DEFAULT_SIGNAL)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        self._conn = _connect(self.db_path)
        schema.ensure_application_id(self._conn)
        self._migrations = schema.apply_migrations(self._conn)
        self._fts = self._fts_available()
        self._pipe = HubPipe(self.db_path, self.signal_path)

    # ------------------------------------------------------------------ write
    def publish(self, source, domain, etype, key, payload=None, idem=None):
        """Enqueue an immutable timeline event. Returns immediately (non-blocking)."""
        payload = payload or {}
        ts = sem.iso_now()
        row = (
            ts,
            sem.micros_now(),
            source,
            domain,
            etype,
            key,
            json.dumps(payload, ensure_ascii=False),
            idem or sem.idem_key(source, domain, etype, key, payload),
        )
        self._pipe.enqueue(row)

    def publish_and_wait(self, *args, **kwargs):
        """publish() + flush; blocks until the core has absorbed the event."""
        self.publish(*args, **kwargs)
        self._pipe.flush()

    def flush(self):
        self._pipe.flush()

    def pipe_stats(self):
        return self._pipe.stats()

    def close(self):
        self._pipe.close()
        self._conn.close()

    # ------------------------------------------------------------------- read
    def timeline(self, domain=None, source=None, etype=None, key=None,
                 since_seconds=None, limit=200, render=False):
        """Read events newest-first. Set render=True for plain sentences."""
        conds, args = [], []
        for col, val in (("domain", domain), ("source", source),
                         ("etype", etype), ("key", key)):
            if val is not None:
                conds.append(f"{col} = ?")
                args.append(val)
        if since_seconds:
            conds.append("ts_micros >= ?")
            args.append(sem.micros_now() - int(since_seconds * 1e6))
        where = ("WHERE " + " AND ".join(conds)) if conds else ""
        rows = [
            dict(r)
            for r in self._conn.execute(
                f"SELECT id, ts, source, domain, etype, key, payload "
                f"FROM timeline {where} ORDER BY ts_micros DESC, id DESC LIMIT ?",
                args + [limit],
            ).fetchall()
        ]
        if render:
            for r in rows:
                r["narrative"] = sem.render(r)
        return rows

    def count(self):
        return self._conn.execute("SELECT COUNT(*) FROM timeline").fetchone()[0]

    # ------------------------------------------------------------------ graph
    def entity_upsert(self, uid, kind=None, name=None, summary=None,
                      attrs=None, embedding=None):
        """Create or update a graph node. embedding = list[float]."""
        now = sem.iso_now()
        vec = sem.pack_vec(embedding) if embedding is not None else None
        existing = self._conn.execute(
            "SELECT uid FROM entities WHERE uid=?", (uid,)
        ).fetchone()
        if existing:
            self._conn.execute(
                "UPDATE entities SET kind=COALESCE(?,kind), name=COALESCE(?,name), "
                "summary=COALESCE(?,summary), attrs=COALESCE(?,attrs), "
                "embedding=COALESCE(?,embedding), updated_ts=? WHERE uid=?",
                (kind, name, summary,
                 json.dumps(attrs) if attrs is not None else None,
                 vec, now, uid),
            )
        else:
            self._conn.execute(
                "INSERT INTO entities (uid,kind,name,summary,attrs,embedding,created_ts,updated_ts) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (uid, kind, name, summary, json.dumps(attrs or {}), vec, now, now),
            )
        self._conn.commit()
        return self.entity(uid)

    def entity(self, uid):
        row = self._conn.execute(
            "SELECT uid,kind,name,summary,attrs,embedding,created_ts,updated_ts "
            "FROM entities WHERE uid=?", (uid,),
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["attrs"] = json.loads(d.get("attrs") or "{}")
        d["vec_dim"] = sem.vec_dim(d.pop("embedding"))
        return d

    def relate(self, src, rel, dst, attrs=None, valid_from=None, valid_to=None,
               publish_event=True):
        now = sem.iso_now()
        self._conn.execute(
            "INSERT INTO relationships (src,rel,dst,attrs,valid_from,valid_to,created_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (src, rel, dst, json.dumps(attrs or {}), valid_from, valid_to, now),
        )
        self._conn.commit()
        if publish_event:
            self._pipe.enqueue((
                sem.iso_now(), sem.micros_now(), "hub", "identity", "related", src,
                json.dumps({"src": src, "rel": rel, "dst": dst}),
                sem.idem_key("hub", "identity", "related", f"{src}>{dst}", {"rel": rel}),
            ))

    def neighbors(self, uid):
        rows = self._conn.execute(
            "SELECT 'out' AS dir, rel, dst AS other FROM relationships WHERE src=? "
            "UNION ALL "
            "SELECT 'in' AS dir, rel, src AS other FROM relationships WHERE dst=?",
            (uid, uid),
        ).fetchall()
        return [
            {"dir": r["dir"], "rel": r["rel"], "entity": self.entity(r["other"]) or {"uid": r["other"]}}
            for r in rows
        ]

    # ------------------------------------------------------------------ docs
    def ingest_document(self, path, domain="personal", embed_fn=None, chunk_size=1400):
        """Read, hash/dedupe, chunk, optionally embed, and link into the graph."""
        path = os.path.expanduser(path)
        try:
            with open(path, "rb") as f:
                raw = f.read()
        except OSError as e:
            raise ValueError(f"cannot read {path}: {e}")

        h = hashlib.sha256(raw).hexdigest()
        existing = self._conn.execute(
            "SELECT id, uid FROM documents WHERE hash=?", (h,)
        ).fetchone()
        if existing:
            return {"status": "dedupe", "document_id": existing["id"], "uid": existing["uid"]}

        text = _decode_text(raw)
        chunks = sem.chunk_text(text, size=chunk_size or 1400)
        uid = "doc:" + h
        now = sem.iso_now()

        cur = self._conn.execute(
            "INSERT INTO documents (uid,path,hash,size_bytes,domain,imported_at) "
            "VALUES (?,?,?,?,?,?)",
            (uid, path, h, len(raw), domain, now),
        )
        doc_id = cur.lastrowid
        self._conn.execute(
            "INSERT OR IGNORE INTO entities (uid,kind,name,summary,attrs,created_ts,updated_ts) "
            "VALUES (?,?,?,?,?,?,?)",
            (uid, "document", os.path.basename(path),
             f"ingested {now} from {path}",
             json.dumps({"path": path, "domain": domain}), now, now),
        )

        embeds = 0
        for c in chunks:
            vec = sem.pack_vec(embed_fn(c["text"])) if embed_fn else None
            inserted = self._conn.execute(
                "INSERT OR IGNORE INTO knowledge_chunks "
                "(doc_id,idx,text,char_count,embedding,hash) VALUES (?,?,?,?,?,?)",
                (doc_id, c["index"], c["text"], c["chars"], vec,
                 hashlib.sha256(c["text"].encode("utf-8")).hexdigest()),
            )
            if vec and inserted.rowcount:
                embeds += 1

        self._conn.commit()
        self._pipe.enqueue((
            sem.iso_now(), sem.micros_now(), "hub", "knowledge", "ingested", path,
            json.dumps({"path": path, "chunks": len(chunks), "hash": h, "bytes": len(raw),
                        "embedded": embeds}),
            sem.idem_key("hub", "knowledge", "ingested", path, {"hash": h}),
        ))
        return {"ok": "ingested", "document_id": doc_id, "uid": uid,
                "chunks": len(chunks), "embedded": embeds}

    def documents(self, domain=None):
        q = "SELECT id, uid, path, hash, size_bytes, domain, imported_at FROM documents"
        args = []
        if domain:
            q += " WHERE domain=?"
            args.append(domain)
        return [dict(r) for r in self._conn.execute(q, args)]

    def search(self, text=None, vector=None, k=5, min_score=0.0):
        """Keyword via FTS5, semantic via cosine when a vector (list) is given."""
        if vector is not None:
            if not isinstance(vector, list):
                vector = sem.unpack_vec(vector)
            if vector is None:
                return []
            hits = []
            rows = self._conn.execute(
                "SELECT id, doc_id, idx, text, embedding FROM knowledge_chunks "
                "WHERE embedding IS NOT NULL",
            ).fetchall()
            for r in rows:
                score = sem.cosine(vector, sem.unpack_vec(r["embedding"]))
                if score >= min_score:
                    hits.append({"chunk_id": r["id"], "doc_id": r["doc_id"],
                                 "idx": r["idx"], "text": r["text"],
                                 "score": round(score, 4)})
            hits.sort(key=lambda x: -x["score"])
            return hits[:k]

        if text and self._fts:
            rows = self._conn.execute(
                "SELECT rowid FROM knowledge_fts WHERE knowledge_fts MATCH ? LIMIT ?",
                (text, k),
            ).fetchall()
            return [self._chunk(r["rowid"]) for r in rows]
        return []

    def _chunk(self, chunk_id):
        r = self._conn.execute(
            "SELECT id, doc_id, idx, text, hash FROM knowledge_chunks WHERE id=?",
            (chunk_id,),
        ).fetchone()
        return dict(r) if r else None

    # ------------------------------------------------------------------ apps
    def app_upsert(self, app_id, name, kind="programme", version="0.0.1",
                   manifest=None, status="active"):
        now = sem.iso_now()
        self._conn.execute(
            "INSERT INTO apps (app_id,name,kind,status,version,manifest,created_at,updated_at) "
            "VALUES (?,?,?,?,?,?,?,?) "
            "ON CONFLICT(app_id) DO UPDATE SET name=excluded.name, kind=excluded.kind, "
            "status=excluded.status, version=excluded.version, manifest=excluded.manifest, "
            "updated_at=excluded.updated_at",
            (app_id, name, kind, status, version, json.dumps(manifest or {}),
             now, now),
        )
        self._conn.commit()
        return self.app(app_id)

    def app(self, app_id):
        r = self._conn.execute("SELECT * FROM apps WHERE app_id=?", (app_id,)).fetchone()
        return dict(r) if r else None

    def apps(self):
        return [dict(r) for r in self._conn.execute(
            "SELECT app_id,name,kind,status,version FROM apps ORDER BY created_at")]

    # ------------------------------------------------------------- telemetry
    def telemetry_push(self, sensor, metric, value, attrs=None, bucket_seconds=None):
        bucket = bucket_seconds if bucket_seconds is not None else (int(time.time()) // 3600) * 3600
        row = self._conn.execute(
            "SELECT count, sum, min, max FROM telemetry "
            "WHERE bucket=? AND sensor=? AND metric=?",
            (bucket, sensor, metric)).fetchone()
        if row:
            self._conn.execute(
                "UPDATE telemetry SET count=count+1, sum=sum+?, min=MIN(min,?), max=MAX(max,?) "
                "WHERE bucket=? AND sensor=? AND metric=?",
                (value, value, value, bucket, sensor, metric))
        else:
            self._conn.execute(
                "INSERT INTO telemetry (bucket,sensor,metric,count,sum,min,max,attrs) "
                "VALUES (?,?,?,1,?,?,?,?)",
                (bucket, sensor, metric, value, value, value,
                 json.dumps({"value": value})))
        self._conn.commit()

    def telemetry_read(self, sensor, metric, buckets=48):
        rows = self._conn.execute(
            "SELECT bucket, count, sum, min, max FROM telemetry "
            "WHERE sensor=? AND metric=? ORDER BY bucket DESC LIMIT ?",
            (sensor, metric, buckets)).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------ projections
    def snapshot(self, name, data):
        """Materialize a derived view into projections (state persistence)."""
        now = sem.iso_now()
        h = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        self._conn.execute(
            "INSERT OR REPLACE INTO projections (name,ts,hash,data) VALUES (?,?,?,?)",
            (name, now, h, json.dumps(data, ensure_ascii=False)))
        self._conn.commit()
        return {"name": name, "ts": now, "hash": h}

    def projection(self, name, limit=1):
        rows = self._conn.execute(
            "SELECT ts, hash, data FROM projections WHERE name=? ORDER BY ts DESC LIMIT ?",
            (name, limit)).fetchall()
        return [dict(r) | {"data": json.loads(r["data"])} for r in rows]

    # ---------------------------------------------------------------- utilities
    def _fts_available(self):
        try:
            self._conn.execute("SELECT rowid FROM knowledge_fts LIMIT 1").fetchall()
            return True
        except sqlite3.Error:
            return False

    def schema_version(self):
        r = self._conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()
        return r[0] or 0

    def stats(self):
        return {
            "schema_version": self.schema_version(),
            "timeline_events": self.count(),
            "entities": self._conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0],
            "relationships": self._conn.execute("SELECT COUNT(*) FROM relationships").fetchone()[0],
            "documents": self._conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
            "knowledge_chunks": self._conn.execute("SELECT COUNT(*) FROM knowledge_chunks").fetchone()[0],
            "apps": self._conn.execute("SELECT COUNT(*) FROM apps").fetchone()[0],
            "projections": self._conn.execute("SELECT COUNT(*) FROM projections").fetchone()[0],
            "fts": self._fts,
            "pipe": self._pipe.stats(),
        }

    def export(self, target=None):
        """Portability: stream a consistent SQLite backup to `target`."""
        target = os.path.expanduser(target or os.path.join(
            os.path.dirname(self.db_path), "exports", "vasub_export.db"))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        self._pipe.flush()
        dst = sqlite3.connect(target)
        with dst:
            self._conn.backup(dst)
        dst.close()
        return target

    def integrity(self):
        try:
            return self._conn.execute("PRAGMA integrity_check").fetchone()[0]
        except sqlite3.Error:
            return "error"