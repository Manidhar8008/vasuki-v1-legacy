from task_router import TaskRouter
from filesystem_agent import FilesystemAgent
from memory_agent import MemoryAgent
from planner_agent import PlannerAgent
from executor_agent import ExecutorAgent
from code_agent import CodeAgent
from project_agent import ProjectAgent
from device_agent import DeviceAgent

fs = FilesystemAgent()
memory = MemoryAgent()
planner = PlannerAgent()
executor = ExecutorAgent()

router = TaskRouter()

code = CodeAgent()
project = ProjectAgent()
device = DeviceAgent()


print("\nVASUKI AGENT BOOT\n")
print("Modules:")
print("- Filesystem")
print("- Memory")
print("- Planner")
print("- Executor")
print("- Code")
print("- Project")
print("- Device")
print("\nStatus: ONLINE\n")


while True:

    cmd = input("vasuki> ").strip()

    if not cmd:
        continue

    if cmd == "exit":
        break

    elif cmd == "think":
        print(router.route(cmd))

    elif cmd == "backup":
        print(router.route(cmd))
	
    elif cmd == "status":
        print(router.route(cmd))

    elif cmd.startswith("search "):
        print(router.route(cmd))

    elif cmd == "ls":
        print(fs.ls("."))

    elif cmd.startswith("read "):
        path = cmd.replace("read ", "", 1)
        print(fs.read(path))

    elif cmd.startswith("write "):

        try:
            payload = cmd.replace("write ", "", 1)

            file_name, content = payload.split("|", 1)

            print(
                fs.write(
                    file_name.strip(),
                    content.strip()
                )
            )

        except:
            print("usage: write file.txt | hello")

    elif cmd.startswith("remember "):

        text = cmd.replace("remember ", "", 1)

        memory.remember(text)

        print("MEMORY STORED")

    elif cmd == "recall":

        rows = memory.recall()

        for r in rows:
            print(r)

    elif cmd.startswith("plan "):

        goal = cmd.replace("plan ", "", 1)

        plan = planner.plan(goal)

        for step in plan:
            print(step)

    elif cmd.startswith("run "):

        command = cmd.replace("run ", "", 1)

        print(
            executor.run(command)
        )

    elif cmd == "room state":

        print(device.room_state())

    elif cmd == "project status":

        print(
            project.status(
                "/data/data/com.termux/files/home/vasuki"
            )
        )

    elif cmd == "largest files":

        print(
            project.largest_files(
                "/data/data/com.termux/files/home/vasuki",
                10
            )
        )

    elif cmd.startswith("explain "):

        file_name = cmd.replace(
            "explain ",
            "",
            1
        )

        print(
            code.explain(file_name)
        )

    elif cmd.startswith("count functions "):

        file_name = cmd.replace(
            "count functions ",
            "",
            1
        )

        print(
            code.count_functions(
                file_name
            )
        )

    elif cmd == "project summary":

        print(
            code.summarize_project(
                "/data/data/com.termux/files/home/vasuki"
            )
        )

    else:
        print("Unknown command")
