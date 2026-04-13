import json
import re

with open('coreason_ontology.schema.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

for def_name, def_schema in schema['$defs'].items():
    for prop_name, prop_schema in def_schema.get('properties', {}).items():
        if 'default' in prop_schema and prop_schema.get('type') == 'string':
            val = prop_schema['default']
            if 'minLength' in prop_schema and len(val) < prop_schema['minLength']:
                print(f'ERROR: {def_name}.{prop_name} default too short: {val}')
            if 'maxLength' in prop_schema and len(val) > prop_schema['maxLength']:
                print(f'ERROR: {def_name}.{prop_name} default too long: {val}')
            if 'pattern' in prop_schema:
                if not re.match(prop_schema['pattern'], val):
                    print(f'ERROR: {def_name}.{prop_name} default {val} does not match pattern {prop_schema["pattern"]}')

print("Check finished.")
