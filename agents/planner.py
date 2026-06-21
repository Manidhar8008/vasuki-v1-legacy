import sqlite3

DB = "/data/data/com.termux/files/home/vasuki/data/vasuki.db"

goal = input("Goal: ")

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute(
"""
INSERT INTO memories
(category,content)
VALUES (?,?)
""",
("goal",goal)
)

conn.commit()

print("Goal stored")
