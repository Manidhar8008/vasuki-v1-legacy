import sqlite3

DB = "/data/data/com.termux/files/home/vasuki/data/vasuki.db"

def remember(category, content):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO memories
        (category,content)
        VALUES (?,?)
        """,
        (category, content)
    )

    conn.commit()
    conn.close()

def recall(category):
    conn = sqlite3.connect(DB)

    cur = conn.cursor()

    cur.execute(
        """
        SELECT content
        FROM memories
        WHERE category=?
        ORDER BY id DESC
        LIMIT 10
        """,
        (category,)
    )

    rows = cur.fetchall()

    conn.close()

    return rows

if __name__ == "__main__":
    remember("goal", "Build Vasuki")

    print(recall("goal"))
