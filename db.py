import sqlite3
from typing import List, Dict, Any


class VasukiDB:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def query(self, sql: str, params: tuple = (), limit: int = 50):
        conn = self.connect()
        cur = conn.cursor()

        try:
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [dict(r) for r in rows[:limit]]
        finally:
            conn.close()

    def execute_raw(self, sql: str):
        conn = self.connect()
        cur = conn.cursor()

        try:
            cur.execute(sql)
            return cur.fetchall()
        finally:
            conn.close()
