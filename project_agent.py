import os


class ProjectAgent:

    def status(self, root):

        py_files = 0
        folders = 0
        total_size = 0

        for path, dirs, files in os.walk(root):

            folders += len(dirs)

            for f in files:

                full = os.path.join(path, f)

                try:
                    total_size += os.path.getsize(full)
                except:
                    pass

                if f.endswith(".py"):
                    py_files += 1

        return {
            "root": root,
            "python_files": py_files,
            "folders": folders,
            "size_mb": round(total_size / 1024 / 1024, 2)
        }

    def largest_files(self, root, limit=10):

        data = []

        for path, dirs, files in os.walk(root):

            for f in files:

                full = os.path.join(path, f)

                try:
                    size = os.path.getsize(full)

                    data.append({
                        "file": full,
                        "size_mb": round(size / 1024 / 1024, 2)
                    })

                except:
                    pass

        data.sort(
            key=lambda x: x["size_mb"],
            reverse=True
        )

        return data[:limit]

    def inventory(self, root):

        result = []

        for item in sorted(os.listdir(root)):

            full = os.path.join(root, item)

            result.append({
                "name": item,
                "type": "dir" if os.path.isdir(full) else "file"
            })

        return result
