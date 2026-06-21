import os
import shutil


class FilesystemAgent:

    def ls(self, path="."):

        try:
            return os.listdir(path)
        except Exception as e:
            return str(e)

    def read(self, path):

        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return str(e)

    def write(self, path, content):

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            return "FILE WRITTEN"

        except Exception as e:
            return str(e)

    def mkdir(self, path):

        try:
            os.makedirs(path, exist_ok=True)
            return "DIRECTORY CREATED"
        except Exception as e:
            return str(e)

    def delete(self, path):

        try:
            os.remove(path)
            return "FILE DELETED"
        except Exception as e:
            return str(e)

    def copy(self, src, dst):

        try:
            shutil.copy(src, dst)
            return "FILE COPIED"
        except Exception as e:
            return str(e)

    def move(self, src, dst):

        try:
            shutil.move(src, dst)
            return "FILE MOVED"
        except Exception as e:
            return str(e)
