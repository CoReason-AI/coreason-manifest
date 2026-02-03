import yaml
import sys
from pathlib import Path

# Ensure src is in python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from coreason_manifest.v2.spec.definitions import ManifestV2

def validate_sample():
    yaml_path = Path("sample_v2.yaml")

    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    try:
        manifest = ManifestV2.model_validate(data)
        print("Validation Successful!")
        print(manifest.model_dump_json(indent=2, by_alias=True))
    except Exception as e:
        print(f"Validation Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    validate_sample()
