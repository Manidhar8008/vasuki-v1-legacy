class ReasoningAgent:

    def think(self, snapshot):

        issues = []
        recommendations = []

        py_files = snapshot.get("python_files", 0)
        size_mb = snapshot.get("size_mb", 0)
        db_size = snapshot.get("db_size_mb", 0)
        free_gb = snapshot.get("free_gb", 999)

        if free_gb < 1:
            issues.append("LOW_STORAGE")
            recommendations.append("DELETE_OLD_BACKUPS")

        if db_size > 50:
            issues.append("DATABASE_GROWTH")
            recommendations.append("OPTIMIZE_DATABASE")

        if py_files > 50:
            issues.append("PROJECT_COMPLEXITY_INCREASING")
            recommendations.append("MAP_CODEBASE")

        health = "HEALTHY"

        if len(issues) >= 1:
            health = "WARNING"

        if len(issues) >= 3:
            health = "CRITICAL"

        return {
            "health": health,
            "issues": issues,
            "recommendations": recommendations
        }
