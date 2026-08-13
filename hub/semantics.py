"""Vasuki Hub - semantics: human-readable timeline, idempotency, vectors."""

import hashlib
import json
import math
import struct
import time
from datetime import datetime, timezone

DOMAIN_LABELS = {
    "system": "system",
    "knowledge": "knowledge",
    "sensor": "sensor",
    "identity": "identity",
    "projects": "projects",
    "life": "life",
    "health": "health",
}


def iso_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def micros_now():
    return time.time_ns() // 1000


def idem_key(source, domain, etype, key, payload):
    """Deterministic key so re-publishing the same logical event is a no-op."""
    canonical = json.dumps(
        {"source": source, "domain": domain, "etype": etype, "key": key, "payload": payload},
        sort_keys=True, ensure_ascii=False, separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def pack_vec(vec):
    """float list -> float32 little-endian bytes (BLOB)."""
    return struct.pack(f"<{len(vec)}f", *vec)


def unpack_vec(blob):
    if not blob:
        return None
    return list(struct.unpack(f"<{len(blob) // 4}f", blob))


def vec_dim(blob):
    return len(blob) // 4 if blob else 0


def cosine(a, b):
    """Cosine similarity between two float lists; 0.0 on degenerate input."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


# ---------------------------------------------------------------------------
# Narrative rendering: turn any timeline row into a plain sentence.
# ---------------------------------------------------------------------------

def render(event):
    """Render a timeline dict into a human-readable sentence."""
    etype = event.get("etype", "event")
    key = event.get("key") or "?"
    domain = event.get("domain", "system")
    try:
        p = json.loads(event.get("payload") or "{}")
    except (TypeError, ValueError):
        p = {}

    label = DOMAIN_LABELS.get(domain, domain)

    def pick(*names, default=None):
        for n in names:
            if p.get(n) is not None:
                return p[n]
        return default

    if etype == "boot":
        return f"boot: {key} started ({p.get('version', '?')})"
    if etype == "ingested":
        return f"ingested {p.get('path') or key} into {label} ({p.get('chunks', 0)} chunks)"
    if etype == "observed":
        v = p.get("value")
        return f"observed {label} {key} = {v}"
    if etype == "created":
        return f"created {label} entity '{key}' ({p.get('kind', '?')})"
    if etype == "related":
        return f"linked {p.get('src')} --[{p.get('rel', '?')}]--> {p.get('dst')}"
    if etype == "updated":
        fields = p.get("fields")
        if isinstance(fields, list) and fields:
            return f"updated {label} {key}: {', '.join(fields)}"
        return f"updated {label} {key}"
    if etype == "drift":
        return f"drift detected in {key} (score {p.get('score', '?')}, {p.get('signals', [])})"
    if etype == "query":
        return f"query '{p.get('text') or key}' answered via {p.get('engine', '?')} ({p.get('hits', 0)} hits)"
    if etype == "decided":
        return f"decision on {key}: {p.get('decision', '?')} (rule {p.get('rule', '?')})"
    if etype == "error":
        return f"error in {key}: {p.get('message', '?')}"
    if etype == "life":
        return f"life note {key}: {p.get('note', '')}"
    if etype == "telemetry":
        return f"telemetry {key}: {p.get('sum', 0):g} over {p.get('count', 0)} samples"
    if etype == "app":
        return f"app event {p.get('kind', '?')} '{p.get('name') or key}' ({p.get('status', '?')})"

    detail = json.dumps(p, ensure_ascii=False)[:120]
    return f"{label} {etype} on {key}: {detail}"


def chunk_text(text, size=1400, overlap=120):
    """Split text into overlapping chunks with token-ish estimates."""
    if not text:
        return []
    text = text.strip()
    if len(text) <= size:
        return [{"index": 0, "text": text, "chars": len(text), "tokens": max(1, len(text) // 4)}]
    chunks = []
    start = 0
    i = 0
    while start < len(text):
        end = min(start + size, len(text))
        piece = text[start:end]
        chunks.append({"index": i, "text": piece, "chars": len(piece), "tokens": max(1, len(piece) // 4)})
        i += 1
        if end >= len(text):
            break
        start = end - overlap
    return chunks