import json

with open('coreason_ontology.schema.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

found = []

for def_name, def_schema in schema['$defs'].items():
    for prop_name, prop_schema in def_schema.get('properties', {}).items():
        if 'enum' in prop_schema:
            t = prop_schema.get('type')
            for val in prop_schema['enum']:
                if t == 'string' and type(val) is not str:
                    found.append(f"{def_name}.{prop_name}: val {val} is not string")
                if t == 'integer' and type(val) is not int:
                    found.append(f"{def_name}.{prop_name}: val {val} is not integer")
                if t == 'number' and type(val) not in (int, float):
                    found.append(f"{def_name}.{prop_name}: val {val} is not number")
                if t == 'boolean' and type(val) is not bool:
                    found.append(f"{def_name}.{prop_name}: val {val} is not boolean")
                if t == 'null' and val is not None:
                    found.append(f"{def_name}.{prop_name}: val {val} is not null")

if not found:
    print("Enum types strictly match the type parameter!")
else:
    for problem in found:
        print(problem)
