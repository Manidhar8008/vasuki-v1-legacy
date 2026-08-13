"""Vasuki Hub - non-blocking event pipe.

`publish()` enqueues an event and returns in microseconds; a single daemon
worker drains the bounded queue and writes it to BOTH the timeline table and
the human-readable room_signal.log. Execution loops never block on disk I/O.
"""

import json
import os
import queue
import sqlite3
import threading
import time

import hub.semantics as sem


def _connect(db_path):
    conn = sqlite3.connect(db_path, timeout=30.0, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


class HubPipe:
    """Thread + bounded queue pipe backing every hub write."""

    def __init__(self, db_path, signal_path, max_queue=5000):
        self._db_path = db_path
        self._signal_path = os.path.expanduser(signal_path)
        self._queue = queue.Queue(maxsize=max_queue)
        self._dropped = 0
        self._writes = 0
        self._lock = threading.Lock()
        self._closed = False
        self._shutdown = object()

        self._writer = threading.Thread(target=self._drain, name="hub-pipe", daemon=True)
        self._writer.start()

    # -- producers (non-blocking) -----------------------------------------
    def enqueue(self, timeline_row):
        """timeline_row must contain ts, ts_micros, source, domain, etype,
        key, payload, idem_key (all resolved). Never blocks the caller."""
        if self._closed:
            raise RuntimeError("hub pipe is closed")
        try:
            self._queue.put_nowait(timeline_row)
        except queue.Full:
            with self._lock:
                self._dropped += 1

    # -- worker ------------------------------------------------------------
    def _drain(self):
        os.makedirs(os.path.dirname(self._signal_path), exist_ok=True)
        conn = _connect(self._db_path)
        signal_f = None
        try:
            signal_f = open(self._signal_path, "a", buffering=1)
        except OSError:
            signal_f = None

        while True:
            item = self._queue.get()
            if item is self._shutdown:
                break

            ts, ts_micros, source, domain, etype, key, payload, idem = item
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO timeline "
                    "(ts, ts_micros, source, domain, etype, key, payload, idem_key) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (ts, ts_micros, source, domain, etype, key, payload, idem),
                )
                conn.commit()
                with self._lock:
                    self._writes += 1
            except sqlite3.Error:
                conn.rollback()

            if signal_f is not None:
                try:
                    line = json.dumps(
                        {"ts": ts, "source": source, "domain": domain,
                         "etype": etype, "key": key, "payload": json.loads(payload)},
                        ensure_ascii=False,
                    )
                    signal_f.write(line + "\n")
                except Exception:
                    pass

            self._queue.task_done()

        try:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        except sqlite3.Error:
            pass
        if signal_f is not None:
            try:
                signal_f.close()
            except OSError:
                pass
        try:
            conn.close()
        except sqlite3.Error:
            pass

    # -- lifecycle -----------------------------------------------------------
    def flush(self, timeout=15.0):
        """Block until the queue is drained (used by tests / graceful stops)."""
        self._queue.join()

    def close(self, timeout=15.0):
        self._queue.join()
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self._queue.put(self._shutdown)
        # queue.join() again to let the worker reach the sentinel
        self._queue.task_done()
        self._writer.join(timeout=timeout)

    def stats(self):
        with self._lock:
            return {
                "queued": self._queue.qsize(),
                "writes": self._writes,
                "dropped": self._dropped,
            }