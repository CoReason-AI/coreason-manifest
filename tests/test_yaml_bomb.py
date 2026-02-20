from pathlib import Path

import pytest

from coreason_manifest.utils.io import ManifestIO, SecurityViolationError


def test_size_limit(tmp_path: Path) -> None:
    # Create a large file
    large_file = tmp_path / "large.yaml"
    # 5MB + 100 bytes
    content = "a: " + "a" * (5 * 1024 * 1024 + 100)
    large_file.write_text(content)

    loader = ManifestIO(root_dir=tmp_path)

    with pytest.raises(SecurityViolationError, match="exceeds limit"):
        loader.load(large_file.name)

def test_depth_limit(tmp_path: Path) -> None:
    # Create deep nesting
    deep_file = tmp_path / "deep.yaml"
    # depth 55
    content = "a:\n"
    for i in range(55):
        content += "  " * (i+1) + "a:\n"
    content += "  " * 56 + "1"

    deep_file.write_text(content)

    loader = ManifestIO(root_dir=tmp_path)

    with pytest.raises(SecurityViolationError, match="depth exceeds limit"):
        loader.load(deep_file.name)

def test_safe_permissions(tmp_path: Path) -> None:
    # Ensure checking permissions doesn't crash on standard files
    # (Mocking permissions is hard without os calls, but we test basic load flow)
    safe_file = tmp_path / "safe.yaml"
    safe_file.write_text("a: 1")

    loader = ManifestIO(root_dir=tmp_path)
    data = loader.load(safe_file.name)
    assert data == {"a": 1}
