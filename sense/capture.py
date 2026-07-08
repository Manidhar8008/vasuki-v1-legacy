#!/usr/bin/env python3
"""
Vasuki Sense Capture v1
Explicit user-triggered camera and microphone capture only.
No background service. No automatic capture. No upload.
"""
from __future__ import annotations

import argparse
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path.home() / "vasuki"
CAPTURES = ROOT / "sense" / "captures"
QUEUE = ROOT / "sense" / "sense_queue.py"

def stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def run(command: list[str]) -> None:
    print("RUN:", " ".join(command))
    subprocess.run(command, check=True)

def queue_file(path: Path) -> None:
    run([
        "python3", str(QUEUE), "scan",
        "--root", str(path.parent),
        "--limit", "1"
    ])

def camera(args) -> None:
    out = CAPTURES / "images" / f"camera_{args.camera_id}_{stamp()}.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)

    # Termux:API command: camera ID is selected explicitly.
    run(["termux-camera-photo", "-c", str(args.camera_id), str(out)])

    if not out.exists() or out.stat().st_size == 0:
        raise RuntimeError(f"Camera capture failed: {out}")

    print("CAPTURED_IMAGE:", out)
    queue_file(out)

def microphone(args) -> None:
    seconds = max(1, min(args.seconds, 60))
    out = CAPTURES / "audio" / f"mic_{stamp()}.wav"
    out.parent.mkdir(parents=True, exist_ok=True)

    print(f"Recording for {seconds} seconds. Recording starts only after this command.")
    run([
        "termux-microphone-record",
        "-f", str(out),
        "-l", str(seconds),
        "-e", "wav"
    ])

    if not out.exists() or out.stat().st_size == 0:
        raise RuntimeError(f"Microphone capture failed: {out}")

    print("CAPTURED_AUDIO:", out)
    queue_file(out)

def main() -> None:
    parser = argparse.ArgumentParser(prog="capture.py")
    sub = parser.add_subparsers(dest="command", required=True)

    camera_cmd = sub.add_parser("camera")
    camera_cmd.add_argument(
        "--camera-id",
        required=True,
        help="Camera ID from: termux-camera-info"
    )
    camera_cmd.set_defaults(func=camera)

    mic_cmd = sub.add_parser("mic")
    mic_cmd.add_argument(
        "--seconds",
        type=int,
        default=10,
        help="1–60 seconds; default 10"
    )
    mic_cmd.set_defaults(func=microphone)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
