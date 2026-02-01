import json
from pathlib import Path

from coreason_manifest.definitions.agent import AgentDefinition
from coreason_manifest.recipes import RecipeManifest


def generate_schemas() -> None:
    schema_dir = Path("src/coreason_manifest/schemas")
    schema_dir.mkdir(parents=True, exist_ok=True)

    # Generate Agent Schema
    agent_schema = AgentDefinition.model_json_schema()
    with open(schema_dir / "agent.schema.json", "w", encoding="utf-8") as f:
        json.dump(agent_schema, f, indent=2)
        f.write("\n")
    print(f"Generated {schema_dir / 'agent.schema.json'}")

    # Generate Recipe Schema
    recipe_schema = RecipeManifest.model_json_schema()
    with open(schema_dir / "recipe.schema.json", "w", encoding="utf-8") as f:
        json.dump(recipe_schema, f, indent=2)
        f.write("\n")
    print(f"Generated {schema_dir / 'recipe.schema.json'}")


if __name__ == "__main__":
    generate_schemas()
