#!/usr/bin/env python3
"""
Vasuki Image Intake v1
Imports one explicitly selected image into the local Sense evidence store.
No camera activation, no background scanning, no upload.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.home() / "vasuki"
DB = ROOT / "sense" / "sense_node.db"
DEST = ROOT / "sense" / "captures" / "images"

def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="Path to one selected image")
    parser.add_argument("--summary", required=True, help="What is visibly shown")
    parser.add_argument("--confidence", type=float, default=1.0)
    parser.add_argument("--priority", type=int, default=6)
    args = parser.parse_args()

    source = Path(args.image).expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"ERROR: image not found: {source}")

    if source.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise SystemExit("ERROR: supported formats: jpg, jpeg, png, webp")

    DEST.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    digest = file_hash(source)

    destination = DEST / f"image_{digest[:16]}{source.suffix.lower()}"
    if not destination.exists():
        shutil.copy2(source, destination)

    details = {
        "source_path": str(source),
        "stored_path": str(destination),
        "sha256": digest,
        "policy": "local-only; explicitly selected image",
        "intake_type": "manual_image_import_v1"
    }

    con = sqlite3.connect(DB)
    cur = con.execute("""
        INSERT INTO observations
        (created_at, modality, summary, details_json, confidence, priority, state)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        created_at,
        "image",
        args.summary.strip(),
        json.dumps(details, ensure_ascii=False),
        max(0.0, min(args.confidence, 1.0)),
        max(0, min(args.priority, 10)),
        "IMPORTED"
    ))
    con.commit()
    con.close()

    print("IMAGE_IMPORTED:", destination)
    print("SHA256:", digest)
    print("OBSERVATION_CREATED:", cur.lastrowid)

if __name__ == "__main__":
    main()
