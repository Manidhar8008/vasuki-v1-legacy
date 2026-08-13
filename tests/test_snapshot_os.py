#!/usr/bin/env python3
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import vasuki_snapshot_os as snap


class TestSnapshotFeedbackLoop(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "test_vasuki.db"
        self.original_db_path = snap.DB_PATH
        snap.DB_PATH = str(self.db_path)
        snap.init_db()

    def tearDown(self):
        snap.DB_PATH = self.original_db_path
        self.tmpdir.cleanup()

    def _events(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT change_type, detail FROM snapshot_events ORDER BY id"
        ).fetchall()
        conn.close()
        return rows

    def _snapshot_count(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
        conn.close()
        return count

    def test_state_excludes_self_referenced_tables(self):
        snap.save_snapshot({"dummy": 1}, "h1")
        snap.log_event("NO_DRIFT", "stable_state")

        state = snap.collect_state()

        self.assertNotIn("snapshots", state)
        self.assertNotIn("snapshot_events", state)
        self.assertNotIn("sqlite_sequence", state)

    def test_consecutive_cycles_do_not_report_drift(self):
        snap.run_cycle()
        snap.run_cycle()

        events = self._events()
        event_types = [t for t, _ in events]

        self.assertEqual(["INIT", "NO_DRIFT"], event_types)
        self.assertEqual(2, self._snapshot_count())

        first, second = self._state_hashes()
        self.assertEqual(first, second)

    def _state_hashes(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT hash FROM snapshots ORDER BY id"
        ).fetchall()
        conn.close()
        return [r[0] for r in rows]

    def test_application_table_drift_still_detected(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS app_widgets (id INTEGER PRIMARY KEY AUTOINCREMENT)"
        )
        conn.commit()
        conn.close()

        snap.run_cycle()
        self.assertEqual(["INIT"], [t for t, _ in self._events()])

        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO app_widgets DEFAULT VALUES")
        conn.commit()
        conn.close()

        snap.run_cycle()

        events = self._events()
        self.assertEqual("INIT", events[0][0])
        self.assertEqual("CHANGE", events[1][0])
        self.assertIn("app_widgets", events[1][1])

        snap.run_cycle()
        event_types = [t for t, _ in self._events()]
        self.assertEqual(["INIT", "CHANGE", "NO_DRIFT"], event_types)


if __name__ == "__main__":
    unittest.main(verbosity=2)