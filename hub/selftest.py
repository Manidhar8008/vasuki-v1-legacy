"""Vasuki Hub self-test - exercises every layer of the unified database."""

import os
import sys
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from hub.vas import Vas
import hub.semantics as sem


def fake_embed_fn(dim=8):
    def _embed(text):
        h = abs(hash(text))
        vec = [(h >> (8 * i)) % 97 / 97.0 for i in range(dim)]
        n = sum(v * v for v in vec) ** 0.5
        return [v / n for v in vec]

    return _embed


def main():
    tmp = tempfile.mkdtemp(prefix="hub_test_")
    db = os.path.join(tmp, "vasub.db")
    signal = os.path.join(tmp, "room_signal.log")

    print("1) boot + migrations")
    hub = Vas(db_path=db, signal_path=signal)
    assert hub.schema_version() == 1, hub.schema_version()
    print(f"   schema_version={hub.schema_version()} fts={'yes' if hub._fts else 'no'}")

    print("2) non-blocking publisher (timeline + room_signal.log)")
    hub.publish("vasuki_os", "system", "boot", "vasuki_os", {"version": "0.1.0"})
    hub.publish("sense", "sensor", "observed", "mic.level", {"value": -12, "unit": "dB"})
    hub.publish("ask", "knowledge", "query", "ai", {"text": "hello", "hits": 2})
    hub.publish_and_wait("hub", "projects", "app", "ask", {"name": "ask", "status": "active"})
    assert hub.count() == 4, hub.count()
    with open(signal) as f:
        lines = f.read().strip().splitlines()
    assert len(lines) == 4, len(lines)
    print(f"   timeline_events={hub.count()} signal_lines={len(lines)}")

    print("3) human-readable timeline")
    narr = hub.timeline(render=True)
    for n in narr:
        print("   ", n["narrative"])

    print("4) knowledge graph")
    hub.entity_upsert("person:manidhar", kind="person", name="Manidhar",
                      summary="owner of the vasuki system")
    hub.entity_upsert("proj:vasuki", kind="project", name="Vasuki")
    hub.relate("proj:vasuki", "owned_by", "person:manidhar", {"role": "creator"})
    nb = hub.neighbors("proj:vasuki")
    assert any(e["entity"]["uid"] == "person:manidhar" for e in nb), nb
    print(f"   neighbors(proj:vasuki)={[(e['rel'], e['entity'].get('uid')) for e in nb]}")

    print("5) document ingestion + semantic search")
    doc = os.path.join(tmp, "notes.txt")
    with open(doc, "w") as f:
        for i in range(30):
            f.write(f"Vasuki keeps a kind memory of Manidhar's projects, databases and gardens. line {i}\n")
    r = hub.ingest_document(doc, domain="personal", embed_fn=fake_embed_fn())
    assert r["ok"] == "ingested" and r["chunks"] > 0, r
    hub.flush()
    r2 = hub.ingest_document(doc, domain="personal", embed_fn=fake_embed_fn())  # dedupe
    assert r2["status"] == "dedupe", r2
    kw = hub.search(text="memory OR person", k=3)
    semb = hub.search(vector=fake_embed_fn()("gardens"), k=3)
    assert len(kw) > 0 and len(semb) > 0
    print(f"   documents={len(hub.documents())} chunks_fts_hits={len(kw)} vector_hits={len(semb)}")

    print("6) apps registry")
    hub.app_upsert("hindsight", "Hindsight", kind="programme", version="0.1.0")
    hub.app_upsert("hindsight", "Hindsight", kind="programme", version="0.2.0")  # update
    assert hub.app("hindsight")["version"] == "0.2.0"
    print("   apps=", [a["app_id"] for a in hub.apps()])

    print("7) telemetry")
    hub.telemetry_push("mic", "level", -10)
    hub.telemetry_push("mic", "level", -14)
    t = hub.telemetry_read("mic", "level")
    assert t[0]["count"] == 2 and t[0]["sum"] == -24
    print(f"   {t[0]}")

    print("8) projections")
    hub.snapshot("state:files", {"count": 41})
    p = hub.projection("state:files")[0]
    assert p["data"]["count"] == 41
    print(f"   {p['ts']} -> {p['data']}")

    print("9) export (portability) + integrity")
    out = hub.export(target=os.path.join(tmp, "export.db"))
    assert os.path.getsize(out) > 0
    hub.flush()
    assert hub.integrity() == "ok"
    print(f"   export={out} bytes={os.path.getsize(out)}")

    hub.close()
    print("\nALL HUB TESTS PASSED")


if __name__ == "__main__":
    main()