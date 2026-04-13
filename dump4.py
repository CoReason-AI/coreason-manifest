import json
with open('coreason_ontology.schema.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)
print(json.dumps(schema["$defs"]["JsonPrimitiveState"], indent=2))
