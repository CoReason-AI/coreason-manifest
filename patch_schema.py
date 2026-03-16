import json

from coreason_manifest.utils.algebra import get_ontology_schema

schema = get_ontology_schema()
with open("coreason_ontology.schema.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(schema, indent=2, ensure_ascii=False) + "\n")
