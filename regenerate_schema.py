import json
from pathlib import Path
from coreason_manifest.definitions.agent import AgentDefinition

schema_path = Path("src/coreason_manifest/schemas/agent.schema.json")
generated_schema = AgentDefinition.model_json_schema()

with open(schema_path, "w", encoding="utf-8") as f:
    json.dump(generated_schema, f, indent=2)
    f.write("\n")  # Add newline at end of file

print(f"Updated schema at {schema_path}")
