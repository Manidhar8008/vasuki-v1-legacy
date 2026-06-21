class PlannerAgent:

    def plan(self, goal):

        goal = goal.lower()

        if "telemetry" in goal:

            return [
                "create sensors",
                "capture events",
                "store data",
                "build snapshots",
                "analyze drift"
            ]

        if "copilot" in goal:

            return [
                "filesystem layer",
                "memory layer",
                "executor layer",
                "planner layer",
                "cli interface"
            ]

        return [
            "analyze goal",
            "decompose tasks",
            "execute tasks",
            "verify result"
        ]
