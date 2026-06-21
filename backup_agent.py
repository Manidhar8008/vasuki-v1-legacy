import os
import shutil
from datetime import datetime


class BackupAgent:

    def backup_db(self):

        src = "/data/data/com.termux/files/home/vasuki/data/vasuki.db"

        if not os.path.exists(src):
            return "DATABASE_NOT_FOUND"

        backup_dir = "/data/data/com.termux/files/home/vasuki/backups"

        os.makedirs(
            backup_dir,
            exist_ok=True
        )

        name = datetime.now().strftime(
            "vasuki_%Y%m%d_%H%M%S.db"
        )

        dst = os.path.join(
            backup_dir,
            name
        )

        shutil.copy2(src, dst)

        return {
            "status": "SUCCESS",
            "file": dst
        }
