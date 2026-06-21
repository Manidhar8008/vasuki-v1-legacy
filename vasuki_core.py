import time
from core.ingest import ingest_batch
from core.extract import extract_batch
from core.enrich import enrich_batch
from core.identity import update_identity
from core.memory import build_memories
from core.kg import build_kg
from core.timeline import build_timeline

def run_cycle():
    print("\n[VASUKI CORE] cycle start")

    # 1. INGEST
    files = ingest_batch(limit=20)

    # 2. EXTRACT TEXT
    texts = extract_batch(files)

    # 3. ENRICH OBSERVATIONS
    enrich_batch(texts)

    # 4. IDENTITY RESOLUTION
    update_identity()

    # 5. MEMORY CREATION
    build_memories()

    # 6. KNOWLEDGE GRAPH
    build_kg()

    # 7. TIMELINE
    build_timeline()

    print("[VASUKI CORE] cycle complete\n")


if __name__ == "__main__":
    while True:
        try:
            run_cycle()
            time.sleep(15)   # controlled backpressure
        except Exception as e:
            print("[ERROR]", e)
            time.sleep(30)

