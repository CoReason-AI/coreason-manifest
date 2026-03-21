import json
from scripts.migrate_v1_to_v2 import migrate_schema

old_schema = {
    "type": "object",
    "properties": {
        "query": {"type": "string"}
    }
}

new_schema = migrate_schema(old_schema)
print(json.dumps(new_schema, indent=2))
