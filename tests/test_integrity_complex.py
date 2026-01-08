# Prosperity-3.0
from pathlib import Path

from coreason_manifest.integrity import IntegrityChecker


def test_large_file_hash(tmp_path: Path) -> None:
    """Test hash calculation for files larger than the chunk size (8192)."""
    src = tmp_path / "src"
    src.mkdir()

    # Create a 20KB file
    large_content = b"a" * 20000
    file_path = src / "large_file.bin"
    with open(file_path, "wb") as f:
        f.write(large_content)

    hash1 = IntegrityChecker.calculate_hash(src)

    # Verify stability
    hash2 = IntegrityChecker.calculate_hash(src)
    assert hash1 == hash2

    # Modify slightly at the end
    with open(file_path, "wb") as f:
        f.write(large_content + b"b")

    hash3 = IntegrityChecker.calculate_hash(src)
    assert hash1 != hash3


def test_deeply_nested_structure(tmp_path: Path) -> None:
    """Test hash calculation for deeply nested directories."""
    src = tmp_path / "src"
    src.mkdir()

    # Create structure: src/level1/level2/level3/file.txt
    nested = src / "level1" / "level2" / "level3"
    nested.mkdir(parents=True)
    (nested / "file.txt").write_text("content")

    hash1 = IntegrityChecker.calculate_hash(src)
    assert hash1

    # Create structure: src/level1/level2/level3_diff/file.txt
    nested2 = src / "level1" / "level2" / "level3_diff"
    nested2.mkdir(parents=True)
    (nested2 / "file.txt").write_text("content")

    hash2 = IntegrityChecker.calculate_hash(src)
    assert hash1 != hash2


def test_unicode_filenames(tmp_path: Path) -> None:
    """Test hash calculation with Unicode filenames."""
    src = tmp_path / "src"
    src.mkdir()

    # Filename with unicode: "café.txt"
    (src / "café.txt").write_text("coffee")

    hash1 = IntegrityChecker.calculate_hash(src)

    # Check stability
    hash2 = IntegrityChecker.calculate_hash(src)
    assert hash1 == hash2

    # Rename to non-unicode "cafe.txt"
    (src / "café.txt").rename(src / "cafe.txt")
    hash3 = IntegrityChecker.calculate_hash(src)

    assert hash1 != hash3
