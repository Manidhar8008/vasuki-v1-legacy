from pathlib import Path

home = Path.home()

with open("catalog.txt","w") as f:
    for p in home.rglob("*"):
        try:
            if p.is_file():
                f.write(f"{p}\n")
        except:
            pass

print("Catalog built")
