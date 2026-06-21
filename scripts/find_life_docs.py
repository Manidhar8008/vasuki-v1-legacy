from pathlib import Path

ROOT = Path.home() / "storage" / "shared"

KEYWORDS = [
    "resume",
    "cv",
    "offer",
    "appointment",
    "joining",
    "experience",
    "salary",
    "payslip",
    "certificate",
    "degree",
    "cognizant",
    "genpact",
    "lunar",
    "business",
    "analyst",
    "internship"
]

for f in ROOT.rglob("*"):
    try:
        if not f.is_file():
            continue

        name = f.name.lower()

        for k in KEYWORDS:
            if k in name:
                print(f)
                break

    except:
        pass
