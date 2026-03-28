import json
import sys
import inspect

sys.path.append("src")

from pydantic.json_schema import models_json_schema

import coreason_manifest.spec.ontology as ontology

models = []
for name, obj in inspect.getmembers(ontology):
    if inspect.isclass(obj) and issubclass(obj, ontology.CoreasonBaseState):
        models.append((obj, "validation"))

_, schema = models_json_schema(
    models, title="CoReason Shared Kernel Ontology", description="The definitive source of truth."
)

with open("coreason_ontology.schema.json", "w") as f:
    json.dump(
        {
            "$defs": schema["$defs"],
            "title": "CoReason Shared Kernel Ontology",
            "description": "CoReason Shared Kernel Ontology\n\nUnified JSON Schema for the Coreason Manifest",
        },
        f,
        indent=2,
    )
    f.write("\n")
