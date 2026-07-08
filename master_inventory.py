import os

root = os.path.expanduser("~")

with open("inventory.txt","w") as f:
    for path,dirs,files in os.walk(root):
        for file in files:
            f.write(os.path.join(path,file)+"\n")

print("Inventory created")

