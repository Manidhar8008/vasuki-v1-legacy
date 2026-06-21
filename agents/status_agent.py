import shutil

total, used, free = shutil.disk_usage("/")

print("\nVASUKI STATUS")

print("FREE GB:", round(free/1024/1024/1024,2))
