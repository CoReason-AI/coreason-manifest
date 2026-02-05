import json
import sys
from pathlib import Path

# Ensure src is in python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from coreason_manifest.spec.v2.definitions import ManifestV2


def generate_schema() -> None:
    output_path = Path("src/coreason_manifest/schemas/coreason-v2.schema.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate schema
    # by_alias=True ensures 'x-design' is used in the schema instead of 'design_metadata'
    schema = ManifestV2.model_json_schema(by_alias=True)

    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)
        f.write("\n")

    print(f"Schema generated at {output_path}")


if __name__ == "__main__":
    generate_schema()
