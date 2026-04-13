import json
import jsonschema

with open("coreason_ontology.schema.json", "r", encoding="utf-8") as f:
    schema = json.load(f)

for def_name, def_schema in schema["$defs"].items():
    if "examples" in def_schema:
        for idx, example_val in enumerate(def_schema["examples"]):
            test_schema = {"$defs": schema["$defs"], "$ref": f"#/$defs/{def_name}"}
            validator = jsonschema.Draft202012Validator(test_schema)
            try:
                validator.validate(example_val)
            except jsonschema.ValidationError as e:
                print(f"FAILED EXAMPLE: {def_name}[{idx}] -> {e.message}")

print("Validation script complete.")
