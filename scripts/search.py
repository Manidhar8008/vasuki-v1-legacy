mport sqlite3
import sys

DB = "/data/data/com.termux/files/home/vasuki/data/vasuki.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

query = " ".join(sys.argv[1:])

cur.execute("""
SELECT filename,path,ai_category,importance
FROM files
WHERE filename LIKE ?
ORDER BY importance DESC
LIMIT 20
""", (f"%{query}%",))

rows = cur.fetchall()

for row in rows:
    print("\n----------------")
    print("FILE:", row[0])
    print("PATH:", row[1])
    print("CATEGORY:", row[2])
    print("IMPORTANCE:", row[3])

conn.close()
