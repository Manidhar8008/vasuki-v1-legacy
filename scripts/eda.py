import sqlite3

DB="/data/data/com.termux/files/home/vasuki/data/vasuki.db"

conn=sqlite3.connect(DB)
cur=conn.cursor()

print("\nTOTAL FILES")
cur.execute("SELECT COUNT(*) FROM file_inventory")
print(cur.fetchone()[0])

print("\nTOP EXTENSIONS")
cur.execute("""
SELECT extension,COUNT(*)
FROM file_inventory
GROUP BY extension
ORDER BY COUNT(*) DESC
LIMIT 20
""")

for row in cur.fetchall():
    print(row)

print("\nLARGEST FILES")
cur.execute("""
SELECT filename,size
FROM file_inventory
ORDER BY size DESC
LIMIT 20
""")

for row in cur.fetchall():
    print(row)
