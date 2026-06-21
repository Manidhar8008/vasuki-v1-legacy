from project_agent import ProjectAgent
from code_agent import CodeAgent


class ProjectScan:

    def scan(self, root):

        project = ProjectAgent()
        code = CodeAgent()

        return {
            "status": project.status(root),
            "summary": code.summarize_project(root),
            "largest_files":
                project.largest_files(root, 5)
        }
