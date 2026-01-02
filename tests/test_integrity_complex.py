# Prosperity-3.0
from pathlib import Path

import pytest

from coreason_manifest.errors import IntegrityCompromisedError
from coreason_manifest.integrity import IntegrityChecker


def test_ignore_git_directory(tmp_path: Path) -> None:
    """Test that .git directory is ignored in hash calculation."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("content")

    hash1 = IntegrityChecker.calculate_hash(src)

    # Add .git directory
    git_dir = src / ".git"
    git_dir.mkdir()
    (git_dir / "HEAD").write_text("ref: refs/heads/main")

    hash2 = IntegrityChecker.calculate_hash(src)

    assert hash1 == hash2


def test_ignore_ds_store(tmp_path: Path) -> None:
    """Test that .DS_Store is ignored."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("content")

    hash1 = IntegrityChecker.calculate_hash(src)

    (src / ".DS_Store").write_text("junk")

    hash2 = IntegrityChecker.calculate_hash(src)

    assert hash1 == hash2


def test_ignore_pycache(tmp_path: Path) -> None:
    """Test that __pycache__ is ignored."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("content")

    hash1 = IntegrityChecker.calculate_hash(src)

    cache_dir = src / "__pycache__"
    cache_dir.mkdir()
    (cache_dir / "main.cpython-312.pyc").write_text("binary")

    hash2 = IntegrityChecker.calculate_hash(src)

    assert hash1 == hash2


def test_symlink_rejection(tmp_path: Path) -> None:
    """Test that symlinks cause an IntegrityCompromisedError."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("content")

    # Create symlink
    target = src / "target"
    target.touch()
    try:
        (src / "link").symlink_to(target)
    except OSError:
        pytest.skip("Symlinks not supported on this platform")

    with pytest.raises(IntegrityCompromisedError) as excinfo:
        IntegrityChecker.calculate_hash(src)
    assert "Symbolic links are forbidden" in str(excinfo.value)


def test_empty_directory(tmp_path: Path) -> None:
    """Test hash of an empty directory."""
    src = tmp_path / "empty"
    src.mkdir()

    # Should not raise error, just return hash of empty sequence
    hash_val = IntegrityChecker.calculate_hash(src)
    assert isinstance(hash_val, str)
    assert len(hash_val) == 64


def test_unicode_filenames(tmp_path: Path) -> None:
    """Test handling of unicode filenames."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "🚀.py").write_text("rocket")

    hash_val = IntegrityChecker.calculate_hash(src)
    assert isinstance(hash_val, str)
