# Prosperity-3.0
from pathlib import Path

import pytest

from coreason_manifest.integrity import IntegrityChecker


def test_ignored_dirs_immutability() -> None:
    """Test that IGNORED_DIRS is immutable and contains required directories."""
    assert isinstance(IntegrityChecker.IGNORED_DIRS, frozenset)
    assert ".git" in IntegrityChecker.IGNORED_DIRS
    assert "__pycache__" in IntegrityChecker.IGNORED_DIRS

    # Attempting to modify should raise AttributeError
    with pytest.raises(AttributeError):
        IntegrityChecker.IGNORED_DIRS.add("malicious_dir")  # type: ignore[attr-defined]


def test_exclusion_determinism(tmp_path: Path) -> None:
    """
    Test that content in ignored directories does not affect the hash.

    This ensures deterministic hashing even if development artifacts exist.
    """
    # 1. Setup base state
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("print('hello')")
    (src_dir / "utils.py").write_text("def foo(): pass")

    base_hash = IntegrityChecker.calculate_hash(src_dir)

    # 2. Add noise to .git
    git_dir = src_dir / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("random config")
    (git_dir / "HEAD").write_text("ref: refs/heads/main")

    hash_with_git = IntegrityChecker.calculate_hash(src_dir)
    assert hash_with_git == base_hash, "Hash changed after adding .git content"

    # 3. Add noise to __pycache__
    cache_dir = src_dir / "__pycache__"
    cache_dir.mkdir()
    (cache_dir / "main.cpython-312.pyc").write_bytes(b"bytecode_noise")

    hash_with_cache = IntegrityChecker.calculate_hash(src_dir)
    assert hash_with_cache == base_hash, "Hash changed after adding __pycache__ content"

    # 4. Add noise to .env (should be ignored)
    (src_dir / ".env").write_text("SECRET=123")

    hash_with_env = IntegrityChecker.calculate_hash(src_dir)
    assert hash_with_env == base_hash, "Hash changed after adding .env file"

    # 5. Verify sensitivity (Control Case)
    # Adding a real file MUST change the hash
    (src_dir / "new_feature.py").write_text("print('new')")

    final_hash = IntegrityChecker.calculate_hash(src_dir)
    assert final_hash != base_hash, "Hash DID NOT change after adding valid source file"


def test_nested_exclusion(tmp_path: Path) -> None:
    """Test that exclusions work even in subdirectories."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    subdir = src_dir / "subdir"
    subdir.mkdir()
    (subdir / "logic.py").write_text("x = 1")

    base_hash = IntegrityChecker.calculate_hash(src_dir)

    # Add .git inside subdir (submodules scenario or just artifacts)
    nested_git = subdir / ".git"
    nested_git.mkdir()
    (nested_git / "stuff").write_text("ignore me")

    # Ideally, IGNORED_DIRS logic applies to directory names anywhere in the tree
    # The current implementation uses os.walk and checks d_name in IGNORED_DIRS
    # So this should be ignored.

    hash_nested = IntegrityChecker.calculate_hash(src_dir)
    assert hash_nested == base_hash, "Hash changed after adding nested .git directory"
