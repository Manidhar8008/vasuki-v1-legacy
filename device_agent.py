import os
import shutil
import subprocess


class DeviceAgent:

    def room_state(self):

        state = {}

        try:
            total, used, free = shutil.disk_usage("/")

            state["storage_total_gb"] = round(total / 1024**3, 2)
            state["storage_free_gb"] = round(free / 1024**3, 2)

        except:
            pass

        try:
            uptime = subprocess.check_output(
                "uptime",
                shell=True,
                text=True
            ).strip()

            state["uptime"] = uptime

        except:
            pass

        try:
            state["vasuki_files"] = len(
                os.listdir(
                    "/data/data/com.termux/files/home/vasuki"
                )
            )
        except:
            pass

        return state
