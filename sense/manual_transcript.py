#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.home() / "vasuki"
SENSE_DB = ROOT / "sense" / "sense_node.db"
TRANSCRIPTS = ROOT / "sense" / "transcripts"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--language", default="en")
    args = parser.parse_args()

    audio = Path(args.audio).expanduser().resolve()
    if not audio.is_file():
        raise SystemExit(f"ERROR: audio file not found: {audio}")

    text = args.text.strip()
    if not text:
        raise SystemExit("ERROR: transcript text cannot be empty")

    TRANSCRIPTS.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    record = {
        "source_path": str(audio),
        "sha256": sha256(audio),
        "created_at": created_at,
        "engine": "manual_transcript_adapter_v1",
        "language": args.language,
        "transcript": text,
        "policy": "local-only; explicit user-provided transcript"
    }

    text_path = TRANSCRIPTS / f"{audio.stem}.txt"
    json_path = TRANSCRIPTS / f"{audio.stem}.json"

    text_path.write_text(text + "\n", encoding="utf-8")
    json_path.write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    con = sqlite3.connect(SENSE_DB)
    cur = con.execute("""
        INSERT INTO observations
        (created_at, modality, summary, details_json, confidence, priority, state)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        created_at,
        "audio",
        f"Transcript: {text[:160]}",
        json.dumps({
            "audio": str(audio),
            "transcript_file": str(text_path),
            "metadata_file": str(json_path),
            "engine": record["engine"],
            "language": args.language,
            "sha256": record["sha256"]
        }, ensure_ascii=False),
        1.0,
        7,
        "TRANSCRIBED"
    ))
    con.commit()
    con.close()

    print("TRANSCRIPT_SAVED:", text_path)
    print("METADATA_SAVED:", json_path)
    print("OBSERVATION_CREATED:", cur.lastrowid)

if __name__ == "__main__":
    main()
