def build_schema_prompt(schema_summary: dict) -> str:
    nodes = "\n".join(f"- {n}" for n in schema_summary["nodes"])
    rels = "\n".join(f"- {r}" for r in schema_summary["relationships"])
    
    return  f"""
Allowed node labels:
{nodes}

Allowed relationship types:
{rels}

Rules:
- Use only the labels and relationships listed above
- Respect relationship direction
- Add LIMIT 25 unless explicitly requested otherwise
"""
