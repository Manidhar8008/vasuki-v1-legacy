import os


class SearchAgent:

    def search_code(self, root, text):

        results = []

        for path, dirs, files in os.walk(root):

            for file in files:

                if not file.endswith(".py"):
                    continue

                full = os.path.join(path, file)

                try:

                    with open(
                        full,
                        "r",
                        encoding="utf-8",
                        errors="ignore"
                    ) as f:

                        for num, line in enumerate(f, start=1):

                            if text.lower() in line.lower():

                                results.append({
                                    "file": full,
                                    "line": num,
                                    "text": line.strip()
                                })

                except:
                    pass

        return results[:50]
