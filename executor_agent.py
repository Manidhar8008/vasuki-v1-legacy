import subprocess


class ExecutorAgent:

    def run(self, cmd):

        try:

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True
            )

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }

        except Exception as e:

            return {
                "error": str(e)
            }
