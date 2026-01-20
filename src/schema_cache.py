import json
from pathlib import Path

_SCHEMA_CACHE = None

SCHEMA_PATH = Path("data/input/neo4j_schema.json")


def load_schema_once() -> dict:
    global _SCHEMA_CACHE

    if _SCHEMA_CACHE is None:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            _SCHEMA_CACHE = json.load(f)

    return _SCHEMA_CACHE 

if __name__ == "__main__":
    schema1 = load_schema_once()
    print("Schema keys:", schema1.keys())

    schema2 = load_schema_once()
    print("Loaded again (should be cached)")
    print("Schema keys:", schema2.keys())
