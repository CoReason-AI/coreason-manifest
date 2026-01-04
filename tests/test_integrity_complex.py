# Prosperity-3.0
import hashlib
from pathlib import Path

from coreason_manifest.integrity import IntegrityChecker


def test_calculate_hash_empty_dir(tmp_path: Path) -> None:
    """Test hash of an empty directory."""
    src = tmp_path / "src"
    src.mkdir()

    # Expected: SHA256 of empty string
    expected = hashlib.sha256().hexdigest()
    assert IntegrityChecker.calculate_hash(src) == expected


def test_calculate_hash_only_ignored_files(tmp_path: Path) -> None:
    """Test that a directory with only ignored files has the same hash as an empty one."""
    src = tmp_path / "src"
    src.mkdir()
    (src / ".DS_Store").write_text("junk")
    (src / "__pycache__").mkdir()
    (src / "__pycache__" / "cache.pyc").write_text("binary")

    expected = hashlib.sha256().hexdigest()
    assert IntegrityChecker.calculate_hash(src) == expected


def test_calculate_hash_deep_nesting(tmp_path: Path) -> None:
    """Test hash calculation with deep nesting."""
    src = tmp_path / "src"
    src.mkdir()

    nested = src / "a" / "b" / "c" / "d"
    nested.mkdir(parents=True)
    (nested / "deep.txt").write_text("deep content")

    # Should not raise recursion error or path issues
    hash_val = IntegrityChecker.calculate_hash(src)
    assert hash_val is not None
    assert len(hash_val) == 64


def test_calculate_hash_special_chars(tmp_path: Path) -> None:
    """Test filenames with spaces and unicode."""
    src = tmp_path / "src"
    src.mkdir()

    (src / "file with spaces.txt").write_text("content")
    (src / "unicodé_filé.txt").write_text("content")

    hash_val = IntegrityChecker.calculate_hash(src)
    assert len(hash_val) == 64


def test_calculate_hash_large_file(tmp_path: Path) -> None:
    """Test hashing of a file larger than the read chunk size (8192)."""
    src = tmp_path / "src"
    src.mkdir()

    # Create a 20KB file
    large_content = b"a" * 20000
    (src / "large.bin").write_bytes(large_content)

    hash_val = IntegrityChecker.calculate_hash(src)

    # Manually calculate expected
    sha = hashlib.sha256()
    # Relative path is "large.bin"
    sha.update("large.bin".encode("utf-8"))
    sha.update(large_content)
    # But wait, the IntegrityChecker hashes the SEQUENCE of hashes?
    # No, it updates the main sha256 object with (rel_path + content) for each file.
    # Let's verify the implementation logic in the test.

    # Re-reading implementation:
    # for path in file_paths:
    #    sha256.update(rel_path)
    #    while chunk: sha256.update(chunk)

    expected_sha = hashlib.sha256()
    expected_sha.update("large.bin".encode("utf-8"))
    expected_sha.update(large_content)

    assert hash_val == expected_sha.hexdigest()
