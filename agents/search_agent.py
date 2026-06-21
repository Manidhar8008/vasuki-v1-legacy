from pathlib import Path

while True:

    q = input("Search: ")

    for f in Path("/data/data/com.termux/files/home").rglob("*"):

        if q.lower() in str(f).lower():

            print(f)

query = input("Search: ")

with open("../catalog.txt","r") as f:
    for line in f:
        if query.lower() in line.lower():
            print(line.strip())

