import os
import stat
import pytest
from pathlib import Path
from coreason_manifest.utils.v2.io import ManifestIO, SecurityViolation

@pytest.fixture
def jail_dir(tmp_path):
    jail = tmp_path / "jail"
    jail.mkdir()
    return jail

def test_load_valid_file(jail_dir):
    (jail_dir / "valid.yaml").write_text("key: value")
    loader = ManifestIO(root_dir=jail_dir)
    data = loader.load("valid.yaml")
    assert data == {"key": "value"}

def test_path_traversal_detection(jail_dir):
    # Create file outside jail
    outside = jail_dir.parent / "outside.yaml"
    outside.write_text("secret: data")

    loader = ManifestIO(root_dir=jail_dir)

    # Try relative path traversal
    with pytest.raises(SecurityViolation, match="Path Traversal Detected"):
        loader.load("../outside.yaml")

    # Try absolute path outside jail
    with pytest.raises(SecurityViolation, match="Path Traversal Detected"):
        loader.load(str(outside.resolve()))

def test_posix_permissions(jail_dir):
    if os.name != "posix":
        pytest.skip("Skipping POSIX permission test on non-POSIX OS")

    unsafe_file = jail_dir / "unsafe.yaml"
    unsafe_file.write_text("danger: true")

    # Make world-writable
    mode = unsafe_file.stat().st_mode
    unsafe_file.chmod(mode | stat.S_IWOTH)

    loader = ManifestIO(root_dir=jail_dir)
    with pytest.raises(SecurityViolation, match="Unsafe Permissions"):
        loader.load("unsafe.yaml")
