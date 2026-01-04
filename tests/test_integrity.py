# Prosperity-3.0
import os
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

import pytest

from coreason_manifest.errors import IntegrityCompromisedError
from coreason_manifest.integrity import IntegrityChecker
from coreason_manifest.models import AgentDefinition


@pytest.fixture
def agent_def_data() -> Dict[str, Any]:
    return {
        "metadata": {
            "id": str(uuid4()),
            "version": "1.0.0",
            "name": "Test Agent",
            "author": "Test Author",
            "created_at": "2023-10-26T12:00:00Z",
        },
        "interface": {"inputs": {}, "outputs": {}},
        "topology": {
            "steps": [],
            "model_config": {"model": "gpt-4", "temperature": 0.5},
        },
        "dependencies": {"tools": [], "libraries": []},
        "integrity_hash": "dummy",
    }


def test_calculate_hash_stable(tmp_path: Path) -> None:
    """Test that hash calculation is stable and deterministic."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "file1.py").write_text("print('hello')")
    (src / "file2.py").write_text("print('world')")

    hash1 = IntegrityChecker.calculate_hash(src)
    hash2 = IntegrityChecker.calculate_hash(src)
    assert hash1 == hash2


def test_calculate_hash_changes(tmp_path: Path) -> None:
    """Test that hash changes if content changes."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "file1.py").write_text("v1")

    hash1 = IntegrityChecker.calculate_hash(src)

    (src / "file1.py").write_text("v2")
    hash2 = IntegrityChecker.calculate_hash(src)

    assert hash1 != hash2


def test_calculate_hash_structure_changes(tmp_path: Path) -> None:
    """Test that hash changes if file name/structure changes."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "file1.py").write_text("v1")
    hash1 = IntegrityChecker.calculate_hash(src)

    # Rename
    (src / "file1.py").rename(src / "file2.py")
    hash2 = IntegrityChecker.calculate_hash(src)

    assert hash1 != hash2


def test_calculate_hash_ignores_files(tmp_path: Path) -> None:
    """Test that ignored files/directories do not affect the hash."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "file1.py").write_text("v1")
    hash1 = IntegrityChecker.calculate_hash(src)

    # Add ignored file
    (src / ".DS_Store").write_text("junk")
    hash2 = IntegrityChecker.calculate_hash(src)
    assert hash1 == hash2


def test_calculate_hash_ignores_directories(tmp_path: Path) -> None:
    """Test that ignored directories do not affect the hash."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "file1.py").write_text("v1")
    hash1 = IntegrityChecker.calculate_hash(src)

    # Add ignored directory and file inside it
    git_dir = src / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("core = ...")

    hash2 = IntegrityChecker.calculate_hash(src)
    assert hash1 == hash2


def test_calculate_hash_symlink_file(tmp_path: Path) -> None:
    """Test that symlinks raise IntegrityCompromisedError."""
    src = tmp_path / "src"
    src.mkdir()
    target = src / "target.txt"
    target.write_text("content")
    link = src / "link.txt"

    try:
        os.symlink(target, link)
    except OSError:
        pytest.skip("Symlinks not supported on this OS/FS")

    with pytest.raises(IntegrityCompromisedError) as excinfo:
        IntegrityChecker.calculate_hash(src)
    assert "Symbolic links are forbidden" in str(excinfo.value)


def test_calculate_hash_symlink_dir(tmp_path: Path) -> None:
    """Test that directory symlinks raise IntegrityCompromisedError."""
    src = tmp_path / "src"
    src.mkdir()
    real_dir = src / "real"
    real_dir.mkdir()
    (real_dir / "file.txt").write_text("content")

    link_dir = src / "link_dir"
    try:
        os.symlink(real_dir, link_dir)
    except OSError:
        pytest.skip("Symlinks not supported on this OS/FS")

    with pytest.raises(IntegrityCompromisedError) as excinfo:
        IntegrityChecker.calculate_hash(src)
    assert "Symbolic links are forbidden" in str(excinfo.value)


def test_calculate_hash_not_found() -> None:
    """Test Error when directory not found."""
    with pytest.raises(FileNotFoundError):
        IntegrityChecker.calculate_hash("non_existent")


def test_verify_success(tmp_path: Path, agent_def_data: Dict[str, Any]) -> None:
    """Test successful verification."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("pass")

    expected_hash = IntegrityChecker.calculate_hash(src)
    agent_def_data["integrity_hash"] = expected_hash
    agent_def = AgentDefinition(**agent_def_data)

    IntegrityChecker.verify(agent_def, src)


def test_verify_mismatch(tmp_path: Path, agent_def_data: Dict[str, Any]) -> None:
    """Test verification failure."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("pass")

    agent_def_data["integrity_hash"] = "wrong_hash"
    agent_def = AgentDefinition(**agent_def_data)

    with pytest.raises(IntegrityCompromisedError) as excinfo:
        IntegrityChecker.verify(agent_def, src)
    assert "Integrity check failed" in str(excinfo.value)


def test_verify_missing_hash(tmp_path: Path, agent_def_data: Dict[str, Any]) -> None:
    """Test verification when manifest has no hash."""
    src = tmp_path / "src"
    src.mkdir()
    agent_def_data["integrity_hash"] = None
    agent_def = AgentDefinition(**agent_def_data)

    with pytest.raises(IntegrityCompromisedError) as excinfo:
        IntegrityChecker.verify(agent_def, src)
    assert "Manifest missing integrity_hash" in str(excinfo.value)
