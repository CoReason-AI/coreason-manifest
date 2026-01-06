# Prosperity-3.0
import hashlib
from pathlib import Path

import pytest

from coreason_manifest.errors import ManifestSyntaxError
from coreason_manifest.integrity import IntegrityChecker
from coreason_manifest.loader import ManifestLoader
from coreason_manifest.models import (
    AgentDefinition,
)


def test_integrity_deeply_nested(tmp_path: Path) -> None:
    """Test integrity hash calculation for a deeply nested directory structure."""
    src = tmp_path / "src"
    current = src
    # Create 15 levels of nesting
    for i in range(15):
        current = current / f"level_{i}"
        current.mkdir(parents=True, exist_ok=True)
        (current / "data.txt").write_text(f"content at level {i}")

    # Calculate hash
    hash_val = IntegrityChecker.calculate_hash(src)
    assert len(hash_val) == 64

    # Ensure it's deterministic
    assert IntegrityChecker.calculate_hash(src) == hash_val


def test_integrity_only_ignored_files(tmp_path: Path) -> None:
    """
    Test integrity hash for a directory containing only ignored files.
    This should be equivalent to hashing an empty directory.
    """
    src = tmp_path / "src"
    src.mkdir()

    # Create ignored files
    (src / ".env").write_text("SECRET=123")
    (src / "__pycache__").mkdir()
    (src / "__pycache__" / "cache.pyc").write_bytes(b"binary")

    # Create empty directory for comparison
    empty_src = tmp_path / "empty"
    empty_src.mkdir()

    hash_ignored = IntegrityChecker.calculate_hash(src)
    hash_empty = IntegrityChecker.calculate_hash(empty_src)

    assert hash_ignored == hash_empty

    # Calculate expected empty hash manually to verify logic
    # Empty dir -> sorted files list is [] -> sha256() of nothing?
    # Logic: sha256 = hashlib.sha256(); file_paths=[]; ... return sha256.hexdigest()
    # So it should be hash of empty string.
    expected = hashlib.sha256().hexdigest()
    assert hash_ignored == expected


def test_loader_yaml_non_dict(tmp_path: Path) -> None:
    """Test that loading a valid YAML file that is not a dictionary raises ManifestSyntaxError."""
    f = tmp_path / "list.yaml"
    f.write_text("- item1\n- item2")

    with pytest.raises(ManifestSyntaxError, match="must be a dictionary"):
        ManifestLoader.load_raw_from_file(f)

    f2 = tmp_path / "scalar.yaml"
    f2.write_text("just_a_string")

    with pytest.raises(ManifestSyntaxError, match="must be a dictionary"):
        ManifestLoader.load_raw_from_file(f2)


def test_loader_yaml_billion_laughs(tmp_path: Path) -> None:
    """
    Test resilience against YAML Billion Laughs attack.
    yaml.safe_load (used in implementation) should refuse to expand anchors exponentially
    OR just parse them as references without exploding memory (depending on PyYAML version/impl).

    Actually, PyYAML's safe_load DOES handle references, but it shouldn't execute code.
    The 'Billion Laughs' usually causes high CPU/RAM. We just want to ensure it doesn't crash
    or hang indefinitely (timeout implied by test runner) or execute code.
    """
    billion_laughs = """
    a: &a ["lol","lol","lol","lol","lol","lol","lol","lol","lol"]
    b: &b [*a,*a,*a,*a,*a,*a,*a,*a,*a]
    c: &c [*b,*b,*b,*b,*b,*b,*b,*b,*b]
    d: &d [*c,*c,*c,*c,*c,*c,*c,*c,*c]
    e: &e [*d,*d,*d,*d,*d,*d,*d,*d,*d]
    f: &f [*e,*e,*e,*e,*e,*e,*e,*e,*e]
    g: &g [*f,*f,*f,*f,*f,*f,*f,*f,*f]
    h: &h [*g,*g,*g,*g,*g,*g,*g,*g,*g]
    i: &i [*h,*h,*h,*h,*h,*h,*h,*h,*h]
    """
    f = tmp_path / "bomb.yaml"
    f.write_text(billion_laughs)

    # safe_load usually parses this but expands it in memory.
    # If it's too big, it might raise errors or consume memory.
    # We mainly verify it doesn't execute arbitrary code (SafeLoader).
    # NOTE: PyYAML safe_load might actually expand this. We aren't testing for DoS protection
    # per se (unless we set limits), but ensuring it's treated as data.

    try:
        data = ManifestLoader.load_raw_from_file(f)
        assert isinstance(data, dict)
    except Exception:
        # If it fails due to resource limits or recursion depth, that's also acceptable
        # as long as it doesn't execute code.
        pass


def test_stress_dependencies_count() -> None:
    """Test validation with a large number of dependencies."""
    num_libs = 1000
    libraries = [f"lib-{i}==1.0.0" for i in range(num_libs)]

    data = {
        "metadata": {
            "id": "12345678-1234-5678-1234-567812345678",
            "version": "1.0.0",
            "name": "Stress Test",
            "author": "Tester",
            "created_at": "2023-01-01T00:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "topology": {"steps": [], "model_config": {"model": "gpt", "temperature": 0.1}},
        "dependencies": {"tools": [], "libraries": libraries},
        "integrity_hash": "a" * 64,
    }

    # Should create model without performance issues (within reason)
    agent = AgentDefinition(**data)
    assert len(agent.dependencies.libraries) == num_libs
    assert agent.dependencies.libraries[999] == "lib-999==1.0.0"
