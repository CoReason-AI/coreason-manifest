# Prosperity-3.0
import os
from pathlib import Path

import pytest
from coreason_manifest.errors import IntegrityCompromisedError
from coreason_manifest.integrity import IntegrityChecker


def test_calculate_hash_nested_ignores(tmp_path: Path) -> None:
    """Test that ignored directories are skipped even when deeply nested."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "valid.txt").write_text("content")

    # Baseline hash
    hash1 = IntegrityChecker.calculate_hash(src)

    # Add nested ignored dir
    nested = src / "folder" / "deep" / ".git"
    nested.mkdir(parents=True)
    (nested / "ignored.txt").write_text("should be ignored")

    hash2 = IntegrityChecker.calculate_hash(src)

    assert hash1 == hash2


def test_calculate_hash_all_ignored_types(tmp_path: Path) -> None:
    """Test all defined ignored directory types."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "valid.txt").write_text("content")
    hash1 = IntegrityChecker.calculate_hash(src)

    for ignored in IntegrityChecker.IGNORED_DIRS:
        d = src / ignored
        if not d.exists():
            d.mkdir()
        (d / "junk.txt").write_text("junk")

    hash2 = IntegrityChecker.calculate_hash(src)
    assert hash1 == hash2


def test_calculate_hash_unicode_filenames(tmp_path: Path) -> None:
    """Test that unicode filenames are handled correctly."""
    src = tmp_path / "src"
    src.mkdir()

    # Files with unicode names
    name1 = "fiel_ñ_❤.txt"
    name2 = "おはよう.py"

    (src / name1).write_text("content1")
    (src / name2).write_text("content2")

    hash1 = IntegrityChecker.calculate_hash(src)
    assert hash1 is not None
    assert len(hash1) == 64  # SHA256 hex digest length


def test_calculate_hash_large_file(tmp_path: Path) -> None:
    """Test hashing of a file larger than the chunk size (8192)."""
    src = tmp_path / "src"
    src.mkdir()

    # 10KB file
    large_content = b"a" * 10240
    (src / "large.bin").write_bytes(large_content)

    hash1 = IntegrityChecker.calculate_hash(src)

    # Modify slightly at the end
    large_content_2 = b"a" * 10239 + b"b"
    (src / "large.bin").write_bytes(large_content_2)

    hash2 = IntegrityChecker.calculate_hash(src)

    assert hash1 != hash2


def test_calculate_hash_empty_directory_ignored(tmp_path: Path) -> None:
    """
    Test that empty directories do not affect the hash
    (since we iterate over files).
    """
    src = tmp_path / "src"
    src.mkdir()
    (src / "file.txt").write_text("content")

    hash1 = IntegrityChecker.calculate_hash(src)

    (src / "empty_folder").mkdir()

    hash2 = IntegrityChecker.calculate_hash(src)

    assert hash1 == hash2


def test_calculate_hash_permission_error(tmp_path: Path) -> None:
    """
    Test behavior when a file is unreadable.
    Note: chmod might not work as expected in all environments (e.g. Windows/some Docker),
    but on standard Linux it should raise PermissionError.
    """
    if os.name == "nt":
        pytest.skip("Skipping permission test on Windows")

    src = tmp_path / "src"
    src.mkdir()
    secret = src / "secret.txt"
    secret.write_text("secret")

    # Remove read permission
    secret.chmod(0o000)

    try:
        with pytest.raises(PermissionError):
            IntegrityChecker.calculate_hash(src)
    finally:
        # Restore permission for cleanup
        secret.chmod(0o644)


def test_calculate_hash_source_is_symlink(tmp_path: Path) -> None:
    """Test that if the source directory itself is a symlink, it raises error."""
    real_src = tmp_path / "real_src"
    real_src.mkdir()
    (real_src / "file.txt").write_text("content")

    link_src = tmp_path / "link_src"
    try:
        os.symlink(real_src, link_src)
    except OSError:
        pytest.skip("Symlinks not supported")

    with pytest.raises(IntegrityCompromisedError) as excinfo:
        IntegrityChecker.calculate_hash(link_src)
    assert "Symbolic links are forbidden" in str(excinfo.value)


def test_calculate_hash_symlinked_directory(tmp_path: Path) -> None:
    """Test that a symlinked directory inside source raises error."""
    src = tmp_path / "src"
    src.mkdir()

    external_dir = tmp_path / "external"
    external_dir.mkdir()
    (external_dir / "bad.txt").write_text("bad")

    link_dir = src / "linked_dir"
    try:
        os.symlink(external_dir, link_dir)
    except OSError:
        pytest.skip("Symlinks not supported")

    with pytest.raises(IntegrityCompromisedError) as excinfo:
        IntegrityChecker.calculate_hash(src)
    assert "Symbolic links are forbidden" in str(excinfo.value)


def test_calculate_hash_ignored_file(tmp_path: Path) -> None:
    """Test that a file listed in IGNORED_DIRS (like .env) is ignored."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "valid.txt").write_text("content")
    hash1 = IntegrityChecker.calculate_hash(src)

    # Create an ignored file
    (src / ".env").write_text("SECRET=123")

    hash2 = IntegrityChecker.calculate_hash(src)

    assert hash1 == hash2
