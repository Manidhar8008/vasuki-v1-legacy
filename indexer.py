from pathlib import Path

root = Path.home()

with open("all_files.txt", "w") as f:
    for p in root.rglob("*"):
        try:
            f.write(str(p) + "\n")
        except:
            pass

print("Indexed")
