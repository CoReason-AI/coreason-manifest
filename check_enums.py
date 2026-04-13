import json

with open('coreason_ontology.schema.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

for def_name, def_schema in schema['$defs'].items():
    for prop_name, prop_schema in def_schema.get('properties', {}).items():
        if 'default' in prop_schema and 'enum' in prop_schema:
            val = prop_schema['default']
            if val not in prop_schema['enum']:
                print(f'ERROR: {def_name}.{prop_name} default {val} not in enum {prop_schema["enum"]}')

print("Enum check complete")
