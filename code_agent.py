import os
import ast


class CodeAgent:

    def explain(self, filepath):

        if not os.path.exists(filepath):
            return "FILE_NOT_FOUND"

        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        lines = len(code.splitlines())

        try:
            tree = ast.parse(code)

            functions = []
            classes = []

            for node in ast.walk(tree):

                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)

                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)

            return {
                "file": filepath,
                "lines": lines,
                "functions": functions,
                "classes": classes,
                "summary":
                    f"{len(functions)} functions, "
                    f"{len(classes)} classes, "
                    f"{lines} lines"
            }

        except Exception as e:
            return {
                "file": filepath,
                "error": str(e)
            }

    def count_functions(self, filepath):

        if not os.path.exists(filepath):
            return 0

        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        try:
            tree = ast.parse(code)

            count = 0

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    count += 1

            return count

        except:
            return 0

    def summarize_project(self, root):

        result = {
            "python_files": 0,
            "total_lines": 0
        }

        for path, dirs, files in os.walk(root):

            for file in files:

                if file.endswith(".py"):

                    result["python_files"] += 1

                    full = os.path.join(path, file)

                    try:
                        with open(full, "r",
                                  encoding="utf-8",
                                  errors="ignore") as f:

                            result["total_lines"] += len(
                                f.readlines()
                            )

                    except:
                        pass

        return result
