import os
import psycopg2

DB_NAME = "vasuki"
DB_USER = "u0_a348"

conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    host="localhost"
)

cur = conn.cursor()

def insert_file(path):
    filename = os.path.basename(path)
    ext = filename.split(".")[-1]

    cur.execute("""
        INSERT INTO files (path, filename, extension)
        VALUES (%s, %s, %s)
        ON CONFLICT (path) DO NOTHING;
    """, (path, filename, ext))

    conn.commit()
    print("Inserted:", filename)


# TEST: insert single file
insert_file("/storage/emulated/0/Download/sample.pdf")
