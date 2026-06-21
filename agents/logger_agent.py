import sqlite3

DB = "/data/data/com.termux/files/home/vasuki/data/vasuki.db"

def log(user, ai):

    conn = sqlite3.connect(DB)

    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO conversations
        (user_input,ai_response)
        VALUES (?,?)
        """,
        (user, ai)
    )

    conn.commit()

    conn.close()
