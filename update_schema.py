import json
from coreason_manifest.utils.algebra import get_ontology_schema

schema = get_ontology_schema()
with open('coreason_ontology.schema.json', 'w') as f:
    json.dump(schema, f, indent=2)
    f.write('\n')
