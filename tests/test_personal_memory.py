#!/usr/bin/env python3
import unittest
from core.personal_memory_store import PersonalMemoryStore

class TestPersonalMemoryStore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = PersonalMemoryStore()

    def test_database_integrity(self):
        self.assertEqual(self.store.integrity(), "ok")

    def test_required_tables_exist(self):
        tables = set(self.store.tables())
        self.assertTrue({"personal_documents", "personal_chunks", "personal_search"}.issubset(tables))

    def test_expected_data_exists(self):
        self.assertGreater(self.store.count("personal_documents"), 0)
        self.assertGreater(self.store.count("personal_chunks"), 0)

    def test_search_empty_query_is_safe(self):
        self.assertEqual(self.store.search(""), [])

    def test_search_returns_list(self):
        result = self.store.search("Vasuki", limit=5)
        self.assertIsInstance(result, list)
        self.assertLessEqual(len(result), 5)

    def test_read_only_database(self):
        with self.assertRaises(Exception):
            with self.store.connect() as con:
                con.execute("CREATE TABLE vasuki_test_write_blocked (x TEXT)")

if __name__ == "__main__":
    unittest.main(verbosity=2)
