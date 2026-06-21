class AskEngine:
    def __init__(self, db):
        self.db = db

    def ask(self, query: str, mode: str = "memory", limit: int = 20):
        
        if mode == "memory":
            return self.db.query(
                "SELECT * FROM memories WHERE content LIKE ? ORDER BY id DESC",
                (f"%{query}%",),
                limit
            )

        if mode == "entity":
            return self.db.query(
                "SELECT * FROM entities WHERE name LIKE ? ORDER BY id DESC",
                (f"%{query}%",),
                limit
            )

        if mode == "all":
            mem = self.db.query(
                "SELECT * FROM memories WHERE content LIKE ? ORDER BY id DESC",
                (f"%{query}%",),
                limit
            )

            ent = self.db.query(
                "SELECT * FROM entities WHERE name LIKE ? ORDER BY id DESC",
                (f"%{query}%",),
                limit
            )

            return {
                "memories": mem,
                "entities": ent
            }

        return []

    def pretty_print(self, results):
        print("\n" + "=" * 60)
        print(f"VASUKI RESULTS")
        print("=" * 60)

        if isinstance(results, dict):
            for k, v in results.items():
                print(f"\n[{k.upper()}]")
                for i, row in enumerate(v, 1):
                    print(f"\n{i}. {row}")
        else:
            for i, row in enumerate(results, 1):
                print(f"\n{i}. {row}")
