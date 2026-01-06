# Prosperity-3.0
from pathlib import Path

import yaml

from coreason_manifest.integrity import IntegrityChecker


def test_integrity_circular_dependency(tmp_path: Path) -> None:
    """
    Demonstrate that if agent.yaml is in the source dir, updating the hash in it changes the directory hash.
    """
    source_dir = tmp_path / "repo"
    source_dir.mkdir()

    # Create some source code
    (source_dir / "main.py").write_text("print('hello')")

    # Create initial manifest without hash
    manifest_path = source_dir / "agent.yaml"
    manifest_data = {
        "metadata": {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "version": "1.0.0",
            "name": "Test",
            "author": "Me",
            "created_at": "2023-01-01T00:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "topology": {"steps": [], "model_config": {"model": "gpt", "temperature": 0.1}},
        "dependencies": {"tools": [], "libraries": []},
        # We need a dummy hash to pass model validation if we were loading it,
        # but here we just test calculation stability.
        "integrity_hash": "a" * 64,
    }

    with open(manifest_path, "w") as f:
        yaml.dump(manifest_data, f)

    # 1. Calculate Hash 1 (EXCLUDING agent.yaml)
    hash1 = IntegrityChecker.calculate_hash(source_dir, exclude_files={manifest_path})

    # 2. Update agent.yaml with Hash 1
    manifest_data["integrity_hash"] = hash1
    with open(manifest_path, "w") as f:
        yaml.dump(manifest_data, f)

    # 3. Calculate Hash 2 (EXCLUDING agent.yaml)
    hash2 = IntegrityChecker.calculate_hash(source_dir, exclude_files={manifest_path})

    print(f"Hash 1: {hash1}")
    print(f"Hash 2: {hash2}")

    # Assertion: This should now PASS (hashes are equal)
    assert hash1 == hash2
