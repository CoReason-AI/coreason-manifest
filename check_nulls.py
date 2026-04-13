import json

with open('coreason_ontology.schema.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

for def_name, def_schema in schema['$defs'].items():
    for prop_name, prop_schema in def_schema.get('properties', {}).items():
        if 'default' in prop_schema and prop_schema['default'] is None:
            if 'anyOf' not in prop_schema and prop_schema.get('type') != 'null':
                print(f'ERROR: {def_name}.{prop_name} default is null but schema is not explicitly nullable: {prop_schema}')

print("Null check finished")
