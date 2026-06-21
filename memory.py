import psycopg2

conn = psycopg2.connect(dbname="vasuki", user="u0_a348", host="localhost")
cur = conn.cursor()

def add_memory(file_id, memory_type, summary):
    cur.execute("""
        INSERT INTO memories (file_id, memory_type, summary)
        VALUES (%s, %s, %s)
    """, (file_id, memory_type, summary))

    conn.commit()

