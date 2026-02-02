import argparse
import json
from pathlib import Path
from neo4j import GraphDatabase
from utils import get_env_variable
import sys

# Map Neo4j property types to simplified types; It is a helper function you write to normalize Neo4j’s internal data types into clean, predictable, JSON-friendly types.
def map_types(types: list[str]) -> str:
    if not types:
        return "Unknown"

    t = types[0]
    return {
        "String": "String",
        "StringArray": "StringArray",
        "Boolean": "Boolean",
        "Float": "Double",
        "Integer": "Integer",
        "Date": "Date",
        "DateTime": "DateTime"
    }.get(t, t)


def _sort_schema(d: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    """
    Return a new mapping where the top‑level keys and each nested property
    map are sorted alphabetically.  Helps guarantee deterministic JSON
    output when the database hasn’t changed.
    """
    print("Exiting from sort Schema")
    return {lbl: dict(sorted(props.items())) for lbl, props in sorted(d.items())}
    

def main():
    print("entering into Main Function")
    parser = argparse.ArgumentParser(description="Export Neo4j schema.")
    parser.add_argument("--output_dir", required=True, help="Path to store neo4j_schema.json")
    args = parser.parse_args()

    try:
        uri = get_env_variable("DB_URL")
        db_name = get_env_variable("DB_NAME")
    except EnvironmentError as e:
        print(f"Error: {e}", file=sys.stderr)
        raise SystemExit(1)

    # ---- auth (uncomment if needed) ----
    # user     = get_env_variable("DB_USER")
    # password = get_env_variable("DB_PASSWORD")
    # driver   = GraphDatabase.driver(uri, auth=(user, password))
    driver   = GraphDatabase.driver(uri, auth=None)

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    with driver.session(database=db_name) as session:
        node_schema = get_node_schema(session)
        rel_schema  = get_relationship_schema(session)

    node_schema = _sort_schema(node_schema)
    rel_schema  = _sort_schema(rel_schema)

    schema = {"NodeTypes": node_schema, "RelationshipTypes": rel_schema}

    out_path = output_dir / "neo4j_schema.json"
    out_path.write_text(json.dumps(schema, indent=2, sort_keys=True))
    print(f"Schema dumped → {out_path}")
    
def get_node_schema(session):
    print("node schema function entered")

    q_props = """
    CALL db.schema.nodeTypeProperties()
    YIELD nodeType, propertyName, propertyTypes
    WHERE nodeType IN [
      ":`Gene`",
      ":`Protein`",
      ":`Transcript`",
      ":`Disease`",
      ":`Drug`",
      ":`Publication`" ,
      ":`Pathway`",
      ":`Metabolite`",
      ":`Tissue`",
      ":`Modified_Protein`",
      ":`Protein_Structure`"
      
    ]
    RETURN nodeType, propertyName, propertyTypes ;
    """

    schema: dict[str, dict[str, str]] = {}

    for rec in session.run(q_props):
        label = rec["nodeType"].strip(":`")
        prop  = rec["propertyName"]
        types_list = rec["propertyTypes"] or []
        types = ", ".join(types_list) if types_list else "Unknown"
        schema.setdefault(label, {})[prop] = types
        
    print("Labels added to schema:")

    return schema


def get_relationship_schema(session):
    print("relationship schema function entered")
    rel_schema = {}

    q = """
    CALL apoc.meta.schema()
    YIELD value
    WITH value
    UNWIND keys(value) AS nodeLabel
    WITH nodeLabel, value[nodeLabel] AS nodeMeta
    WHERE nodeMeta.type = "node"
      AND nodeLabel IN [
        "Gene","Protein","Transcript","Disease","Drug","Publication" ,"Pathway",
      "Metabolite",
      "Tissue",
      "Modified_Protein",
      "Protein_Structure"
      ]
    UNWIND keys(nodeMeta.relationships) AS relType
    WITH
      relType,
      nodeLabel AS sourceLabel,
      nodeMeta.relationships[relType] AS rmeta
    UNWIND rmeta.labels AS targetLabel
    WITH
      relType,
      sourceLabel,
      rmeta.direction AS direction,
      targetLabel
    WHERE targetLabel IN [
      "Gene","Protein","Transcript","Disease","Drug","Publication" ,"Pathway",
      "Metabolite",
      "Tissue",
      "Modified_Protein",
      "Protein_Structure"
    ]
    RETURN DISTINCT
      relType AS relationshipType,
      CASE direction
        WHEN "out" THEN sourceLabel
        ELSE targetLabel
      END AS startLabel,
      CASE direction
        WHEN "out" THEN targetLabel
        ELSE sourceLabel
      END AS endLabel
    ORDER BY relationshipType
    """

    result = session.run(q, timeout=10)

    for rec in result:
        rel_type = rec["relationshipType"]
        start = rec["startLabel"]
        end = rec["endLabel"]

        rel_schema[rel_type] = {
            "_endpoints": [start, end]
        }

    result.consume()
    
    return rel_schema


if __name__ == "__main__":
    main()
    
    
# def get_node_schema(session):
#     print("node schema function entered")
#     """
#     Return a dict[label -> {property -> type}] that includes *all* labels,
#     even when no nodes for that label currently store properties.
#     """
#     # 1) gather property definitions
#     q_props = """
#     CALL db.schema.nodeTypeProperties()
#     YIELD nodeType, propertyName, propertyTypes
#     RETURN nodeType, propertyName, propertyTypes
#     """
#     schema: dict[str, dict[str, str]] = {}
#     for rec in session.run(q_props):
#         label = rec["nodeType"].strip(":`")
#         prop  = rec["propertyName"]
#         types_list = rec["propertyTypes"] or []
#         types = ", ".join(types_list) if types_list else "Unknown"
#         schema.setdefault(label, {})[prop] = types

#     # 2) make sure labels with *no* properties are still represented
#     q_labels = "CALL db.labels() YIELD label RETURN label"
#     for rec in session.run(q_labels):
#         label = rec["label"]
#         schema.setdefault(label, {})  # leave value dict empty
#         print("label added to schema:")

#     return schema

# def get_node_schema(session):
#     print("Entering into get_node_schema")
#     return {rec["label"]: {} for rec in session.run("CALL db.labels() YIELD label RETURN label")}


# def get_relationship_schema(session):
#     rel_schema = {}

#     q = """
#     CALL apoc.meta.schema()
#     YIELD value
#     RETURN value
#     """

#     result = session.run(q, timeout=10)
#     schema = result.single()["value"]
#     result.consume()

#     for name, meta in schema.items():
#         if meta.get("type") != "relationship":
#             continue

#         # endpoints
#         # src and tgt are lists; take first element, starting with "Unknown" if empty, just in case
#         src = meta.get("start", ["Unknown"])
#         tgt = meta.get("end", ["Unknown"])
#         #rel_schema[name] gives access to the dictionary for that relationship type
#         rel_schema[name] = {
#             "_endpoints": [src[0], tgt[0]]
#         }

#         # properties
#         props = meta.get("properties", {})
#         for prop, prop_meta in props.items():
#             neo4j_type = prop_meta.get("type")
#             rel_schema[name][prop] = map_types([neo4j_type]) 
            
#             # -------- ADD THIS BLOCK (endpoint reconstruction) --------
#     for node_label, meta in schema.items():
#         # skip relationship entries
#         if meta.get("type") == "relationship":
#             continue

#         rels = meta.get("relationships", {})
#         for rel, rmeta in rels.items():
#             if rel not in rel_schema:
#                 continue

#             direction = rmeta.get("direction")
#             labels = rmeta.get("labels", [])

#             if not labels:
#                 continue

#             other = labels[0]

#             if direction == "out":
#                 rel_schema[rel]["_endpoints"] = [node_label, other]
#             elif direction == "in":
#                 rel_schema[rel]["_endpoints"] = [other, node_label]


#     return rel_schema


''' 
def get_relationship_schema(session):
    print("relationship schema function entered")
    """
    For each relationship type return its property map and a sampled endpoint
    pair.  Includes relationship types that have zero properties.
    """
    rel_schema: dict[str, dict[str, str]] = {}

    # 1) property definitions (may return zero rows for prop‑less rel‑types)
    q_props = """
    CALL db.schema.relTypeProperties()
    YIELD relType, propertyName, propertyTypes
    RETURN relType, propertyName, propertyTypes
    """
    for rec in session.run(q_props):
        rtype = rec.get("relType")
        if not rtype:
            # skip malformed rows
            continue
        rtype = rtype.strip(":`")
        prop  = rec.get("propertyName")
        rel_schema.setdefault(rtype, {})          # ensure the key exists
        if prop:
            types_list = rec.get("propertyTypes") or []
            types = ", ".join(types_list) if types_list else "Unknown"
            rel_schema[rtype][prop] = types

    # 2) add rel‑types that have *no* properties at all
    q_all = "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"
    for rec in session.run(q_all):
        rtype = rec["relationshipType"]
        rel_schema.setdefault(rtype, {})

    # 3) sample endpoints for every relationship type
    for rtype in rel_schema:
        q_sample = f'''
        # MATCH (s)-[r:`{rtype}`]->(t)
        # WITH head(labels(s)) AS src, head(labels(t)) AS tgt, elementId(r) AS rid
        # ORDER BY rid
        # RETURN src, tgt
        # LIMIT 1
'''
        rec = session.run(q_sample).single()
        if rec:
            rel_schema[rtype]["_endpoints"] = [rec["src"], rec["tgt"]]
        else:
            rel_schema[rtype]["_endpoints"] = ["Unknown", "Unknown"]
        print("relationship type added to schema:")

    return rel_schema 
'''
# def get_relationship_schema(session):
#     print("Entering into get_relationship_schema")
#     q = """
#     CALL db.relationshipTypes() YIELD relationshipType
#     WITH relationshipType
#     CALL {
#       WITH relationshipType
#       MATCH (s)-[r]->(t)
#       WHERE type(r) = relationshipType
#       RETURN
#         head(labels(s)) AS src,
#         relationshipType AS rel,
#         head(labels(t)) AS tgt
#       LIMIT 1
#     }
#     RETURN src, rel, tgt
#     """

#     rels = {}
#     for rec in session.run(q):
#         rels[rec["rel"]] = {
#             "_endpoints": [rec["src"], rec["tgt"]]
#         }

#     return rels



