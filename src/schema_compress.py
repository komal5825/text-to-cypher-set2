
def compress_schema(schema_json: dict) -> dict:
    """
    Expected schema_json format (example):
    {
      "nodes": {
        "Drug": ["id", "name"],
        "Disease": ["id", "name"]
      },
      "relationships": {
        "DRUG_TREATS_DISEASE": {
          "from": "Drug",
          "to": "Disease"
        }
      }
    }
    """

    nodes = list(schema_json.get("nodes", {}).keys())
    relationships = []

    for rel, meta in schema_json.get("relationships", {}).items():
        relationships.append(
            f"{rel} ({meta['from']} -> {meta['to']})"
        )

    return {
        "nodes": nodes,
        "relationships": relationships
    }
