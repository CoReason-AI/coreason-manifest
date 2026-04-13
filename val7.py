import json
import jsonschema

with open('coreason_ontology.schema.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

defs = schema.get('$defs', {})
wrapper = {
    '$schema': 'http://json-schema.org/draft-07/schema#',
    'title': schema.get('title', 'Ontology'),
    'description': schema.get('description', ''),
    'type': 'object',
    'properties': {name: {'$ref': f'#/$defs/{name}'} for name in defs},
    '$defs': defs,
}

for def_name, def_schema in wrapper["$defs"].items():
    if "properties" in def_schema:
        for prop_name, prop_schema in def_schema["properties"].items():
            if "default" in prop_schema:
                default_val = prop_schema["default"]
                
                test_schema = {
                    "$defs": wrapper["$defs"],
                    "$ref": f"#/$defs/{def_name}/properties/{prop_name}"
                }
                
                validator = jsonschema.Draft7Validator(test_schema)
                try:
                    validator.validate(default_val)
                except jsonschema.ValidationError as e:
                    print(f"FAILED DEFAULT: {def_name}.{prop_name} -> {default_val!r} | Error: {e.message}")

    if "examples" in def_schema:
        for idx, example_val in enumerate(def_schema["examples"]):
            test_schema = {"$defs": wrapper["$defs"], "$ref": f"#/$defs/{def_name}"}
            validator = jsonschema.Draft7Validator(test_schema)
            try:
                validator.validate(example_val)
            except jsonschema.ValidationError as e:
                print(f"FAILED EXAMPLE: {def_name}[{idx}] -> {e.message}")

print("Validation script complete.")
