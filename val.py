import json
import jsonschema
from referencing import Registry, Resource

with open('coreason_ontology.schema.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

# Create a registry for the entire schema so $refs can resolve
resource = Resource.from_contents(schema)
registry = Registry().with_resource(uri="http://example.com/schema", resource=resource)

validator_cls = jsonschema.validators.validator_for(schema)

defs = schema.get('$defs', {})
for def_name, def_schema in defs.items():
    if 'properties' in def_schema:
        for prop_name, prop_schema in def_schema['properties'].items():
            if 'default' in prop_schema:
                default_val = prop_schema['default']
                
                # We validate the default value against the property schema
                try:
                    validator = validator_cls(prop_schema, registry=registry)
                    validator.validate(instance=default_val)
                except jsonschema.ValidationError as e:
                    print(f'ValidationError in {def_name}.{prop_name}: default {default_val!r} does not match type. Error: {e.message}')
