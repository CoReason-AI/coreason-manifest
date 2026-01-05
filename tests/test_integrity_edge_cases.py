# Prosperity-3.0
from pathlib import Path
from typing import Any
from unittest.mock import patch

from coreason_manifest.integrity import IntegrityChecker


def test_chunk_boundary(tmp_path: Path) -> None:
    """
    Test hash calculation for files exactly at and crossing the chunk boundary (8192 bytes).
    """
    src = tmp_path / "src"
    src.mkdir()

    # Exactly 8192 bytes
    (src / "exact.bin").write_bytes(b"a" * 8192)
    hash_exact = IntegrityChecker.calculate_hash(src)

    # 8193 bytes
    (src / "plus_one.bin").write_bytes(b"a" * 8193)
    hash_plus_one = IntegrityChecker.calculate_hash(src)

    assert hash_exact != hash_plus_one


def test_spaces_in_filenames(tmp_path: Path) -> None:
    """Test that files with spaces are handled correctly."""
    src = tmp_path / "src"
    src.mkdir()

    (src / "file with spaces.txt").write_text("content")
    hash1 = IntegrityChecker.calculate_hash(src)

    # Verify strictness: "file with spaces.txt" != "file_with_spaces.txt"
    (src / "file with spaces.txt").rename(src / "file_with_spaces.txt")
    hash2 = IntegrityChecker.calculate_hash(src)

    assert hash1 != hash2


def test_sorting_determinism(tmp_path: Path) -> None:
    """
    Test that the hash is deterministic even if os.walk returns files in different orders.
    We mock os.walk to return files reversed or shuffled.
    """
    src = tmp_path / "src"
    src.mkdir()

    # Create multiple files
    files = ["a.txt", "b.txt", "c.txt"]
    for f in files:
        (src / f).write_text(f"content of {f}")

    # Baseline hash
    expected_hash = IntegrityChecker.calculate_hash(src)

    # Custom walker that yields files in reverse order
    def reverse_walker(top: str | Path, topdown: bool = True) -> Any:
        # We need to simulate os.walk behavior for this specific directory
        # yield (root, dirs, files)
        # root is str(src), dirs is [], files is ["c.txt", "b.txt", "a.txt"]
        yield (str(src), [], reversed(files))

    with patch("os.walk", side_effect=reverse_walker):
        reversed_hash = IntegrityChecker.calculate_hash(src)

    assert reversed_hash == expected_hash, "Hash should be independent of directory listing order"


def test_dotfiles_included(tmp_path: Path) -> None:
    """
    Test that dotfiles NOT in the ignore list are included in the hash.
    e.g., .config, .custom
    """
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print(1)")

    base_hash = IntegrityChecker.calculate_hash(src)

    # Add a non-ignored dotfile
    (src / ".config").write_text("config=1")

    new_hash = IntegrityChecker.calculate_hash(src)

    assert new_hash != base_hash, "Dotfiles not in ignore list MUST affect the hash"


def test_case_sensitivity(tmp_path: Path) -> None:
    """
    Test that file names are case-sensitive in the hash.
    """
    src = tmp_path / "src"
    src.mkdir()

    (src / "test.txt").write_text("content")
    hash_lower = IntegrityChecker.calculate_hash(src)

    (src / "test.txt").rename(src / "Test.txt")
    hash_upper = IntegrityChecker.calculate_hash(src)

    assert hash_lower != hash_upper, "Hash must be case-sensitive regarding filenames"
