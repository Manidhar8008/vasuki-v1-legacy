import sqlite3
from datetime import datetime

DB = "/data/data/com.termux/files/home/vasuki/data/vasuki.db"


class MemoryAgent:

    def __init__(self):
        self.conn = sqlite3.connect(DB)

        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_memory(
            id INTEGER PRIMARY KEY,
            ts TEXT,
            event TEXT,
            result TEXT
        )
        """)

        self.conn.commit()

    def remember(self, text):

        self.conn.execute(
            """
            INSERT INTO agent_memory(
                ts,event,result
            )
            VALUES(?,?,?)
            """,
            (
                datetime.now().isoformat(),
                text,
                "stored"
            )
        )

        self.conn.commit()

        return "MEMORY STORED"

    def recall(self, limit=20):

        cur = self.conn.cursor()

        cur.execute(
            """
            SELECT id,ts,event
            FROM agent_memory
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        )

        return cur.fetchall()
