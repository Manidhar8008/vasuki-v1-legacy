from backup_agent import BackupAgent
from search_agent import SearchAgent
from memory_agent import MemoryAgent
from project_scan import ProjectScan
from reasoning_agent import ReasoningAgent
from status_agent import StatusAgent

class TaskRouter:

    def __init__(self):

        self.backup = BackupAgent()
        self.search = SearchAgent()
        self.memory = MemoryAgent()
        self.scan = ProjectScan()
        self.reasoning = ReasoningAgent()
	self.status_agent = StatusAgent()

        self.root = "/data/data/com.termux/files/home/vasuki"

    def route(self, command):

        cmd = command.strip()
	if cmd == "status":
    return self.status_agent.status()

        # ------------------
        # backup
        # ------------------

        if cmd == "backup":
            return self.backup.backup_db()

        # ------------------
        # search
        # ------------------

        if cmd.startswith("search "):

            text = cmd.replace("search ", "", 1)

            return self.search.search_code(
                self.root,
                text
            )

        # ------------------
        # think
        # ------------------

        if cmd == "think":

            project = self.scan.scan(self.root)

            db_size = 0

            try:
                db_size = project["largest_files"][0]["size_mb"]
            except:
                pass

            snapshot = {
                "python_files":
                    project["summary"]["python_files"],

                "size_mb":
                    project["status"]["size_mb"],

                "db_size_mb":
                    db_size,

                "free_gb":
                    0
            }

            return self.reasoning.think(snapshot)

        return {
            "error": "UNKNOWN_COMMAND"
        }
