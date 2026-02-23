import os
import stat
from pathlib import Path

import pytest

from coreason_manifest.utils.io import ManifestIO, SecurityViolationError


@pytest.fixture
def jail_dir(tmp_path: Path) -> Path:
    jail = tmp_path / "jail"
    jail.mkdir()
    return jail


def test_load_valid_file(jail_dir: Path) -> None:
    (jail_dir / "valid.yaml").write_text("key: value")
    loader = ManifestIO(root_dir=jail_dir)
    data = loader.load("valid.yaml")
    assert data == {"key": "value"}


def test_path_traversal_detection(jail_dir: Path) -> None:
    # Create file outside jail
    outside = jail_dir.parent / "outside.yaml"
    outside.write_text("secret: data")

    loader = ManifestIO(root_dir=jail_dir)

    # Try relative path traversal
    with pytest.raises(SecurityViolationError, match="Path Traversal Detected"):
        loader.load("../outside.yaml")

    # Try absolute path outside jail
    with pytest.raises(SecurityViolationError, match="Path Traversal Detected"):
        loader.load(str(outside.resolve()))


def test_posix_permissions(jail_dir: Path) -> None:
    if os.name != "posix":
        pytest.skip("Skipping POSIX permission test on non-POSIX OS")

    unsafe_file = jail_dir / "unsafe.yaml"
    unsafe_file.write_text("danger: true")

    # Make world-writable
    mode = unsafe_file.stat().st_mode
    unsafe_file.chmod(mode | stat.S_IWOTH)

    loader = ManifestIO(root_dir=jail_dir)
    with pytest.raises(SecurityViolationError, match="Unsafe Permissions"):
        loader.load("unsafe.yaml")


def test_manifest_io_eloop_enoent() -> None:
    """Cover lines 60-63 in io.py: ELOOP and ENOENT handling."""
    import errno
    from unittest.mock import patch, MagicMock

    loader = ManifestIO(root_dir=Path("/tmp"))

    # Mock os.lstat to succeed so we reach os.open
    # We must configure mock_lstat to return a valid-looking stat object
    # because Path.resolve calls it and expects integer st_mode.
    mock_stat = MagicMock()
    mock_stat.st_mode = 0o100644  # Regular file
    mock_stat.st_ino = 12345
    mock_stat.st_dev = 1

    with patch("os.lstat", return_value=mock_stat) as mock_lstat:
        # Mock os.open to raise ELOOP
        with patch("os.open") as mock_open:
            mock_open.side_effect = OSError(errno.ELOOP, "Too many symlinks")
            with pytest.raises(SecurityViolationError) as exc_sec:
                loader.read_text("loop.txt")
            assert "Symlink detected" in str(exc_sec.value)

    # Mock os.lstat to succeed (race condition simulation where file vanishes)
    with patch("os.lstat", return_value=mock_stat) as mock_lstat:
        with patch("os.open") as mock_open:
            mock_open.side_effect = OSError(errno.ENOENT, "No such file")
            with pytest.raises(FileNotFoundError):
                loader.read_text("missing.txt")

    # Mock os.lstat to succeed
    with patch("os.lstat", return_value=mock_stat) as mock_lstat:
        with patch("os.open") as mock_open:
            mock_open.side_effect = OSError(errno.EACCES, "Permission denied")
            with pytest.raises(OSError, match="Permission denied") as exc_os:
                loader.read_text("locked.txt")
            assert exc_os.value.errno == errno.EACCES


def test_loader_ast_import_from_banned(tmp_path: Path) -> None:
    """Cover line 103 in loader.py: banned 'from X import Y'."""
    from coreason_manifest.utils.loader import RuntimeSecurityWarning, load_agent_from_ref

    file_path = tmp_path / "banned.py"
    file_path.write_text("from os import path\nclass Agent: pass")
    file_path.chmod(0o600)  # Secure permissions

    with pytest.warns(RuntimeSecurityWarning, match="Dynamic Code Execution"):
        load_agent_from_ref(f"{file_path.name}:Agent", root_dir=tmp_path)


def test_loader_ast_relative_import(tmp_path: Path) -> None:
    """Cover relative imports which have no node.module."""
    import contextlib

    from coreason_manifest.utils.loader import load_agent_from_ref

    file_path = tmp_path / "relative.py"
    # 'from . import sibling' -> node.module is None
    file_path.write_text("from . import sibling\nclass Agent: pass")
    file_path.chmod(0o600)  # Secure permissions

    with contextlib.suppress(ValueError, ImportError, ModuleNotFoundError):
        load_agent_from_ref(f"{file_path.name}:Agent", root_dir=tmp_path)


def test_loader_banned_call(tmp_path: Path) -> None:
    """Cover banned calls like exec/eval."""
    from coreason_manifest.utils.loader import RuntimeSecurityWarning, load_agent_from_ref

    file_path = tmp_path / "banned_call.py"
    file_path.write_text("class Agent:\n    def run(self): eval('1+1')")
    file_path.chmod(0o600)  # Secure permissions

    with pytest.warns(RuntimeSecurityWarning, match="Dynamic Code Execution"):
        load_agent_from_ref(f"{file_path.name}:Agent", root_dir=tmp_path)


def test_loader_not_a_class(tmp_path: Path) -> None:
    """Cover line 211 failure case."""
    from coreason_manifest.utils.loader import load_agent_from_ref

    file_path = tmp_path / "not_class.py"
    file_path.write_text("NotAgent = 'just a string'")
    file_path.chmod(0o600)  # Secure permissions

    with pytest.raises(TypeError) as exc:
        load_agent_from_ref(f"{file_path.name}:NotAgent", root_dir=tmp_path)
    assert "is not a class" in str(exc.value)


def test_loader_success(tmp_path: Path) -> None:
    """Cover line 211 success case."""
    from coreason_manifest.utils.loader import load_agent_from_ref

    file_path = tmp_path / "good.py"
    file_path.write_text("class Agent:\n    pass")
    file_path.chmod(0o600)  # Secure permissions

    cls = load_agent_from_ref(f"{file_path.name}:Agent", root_dir=tmp_path)
    assert cls.__name__ == "Agent"

def test_init_strict_security_missing_nofollow(jail_dir: Path) -> None:
    """Test that strict_security=True raises EnvironmentError when O_NOFOLLOW is missing."""
    from unittest.mock import patch

    # Patch the os module imported in coreason_manifest.utils.io
    with patch("coreason_manifest.utils.io.os", autospec=True) as mock_os:
        # Simulate O_NOFOLLOW missing
        del mock_os.O_NOFOLLOW

        with pytest.raises(EnvironmentError, match="Host OS lacks O_NOFOLLOW support"):
            ManifestIO(root_dir=jail_dir, strict_security=True)


def test_init_relaxed_security_missing_nofollow(jail_dir: Path) -> None:
    """Test that strict_security=False warns when O_NOFOLLOW is missing."""
    from unittest.mock import patch

    with patch("coreason_manifest.utils.io.os", autospec=True) as mock_os:
        del mock_os.O_NOFOLLOW

        with pytest.warns(RuntimeWarning, match="TOCTOU protections disabled"):
             ManifestIO(root_dir=jail_dir, strict_security=False)


def test_read_text_uses_nofollow(jail_dir: Path) -> None:
    """Test that read_text uses O_NOFOLLOW flag."""
    if not hasattr(os, "O_NOFOLLOW"):
        pytest.skip("Test requires O_NOFOLLOW support")

    from unittest.mock import patch

    loader = ManifestIO(root_dir=jail_dir)
    target_file = jail_dir / "test.txt"
    target_file.write_text("content")

    # Patch os.open in coreason_manifest.utils.io
    with patch("coreason_manifest.utils.io.os.open", side_effect=os.open) as mock_open:
        loader.read_text("test.txt")

        args, _ = mock_open.call_args
        flags = args[1]
        assert flags & os.O_NOFOLLOW, "O_NOFOLLOW flag missing in os.open call"


def test_post_open_check_detects_swap(jail_dir: Path) -> None:
    """Test that file swap between lstat and fstat is detected."""
    from unittest.mock import patch, MagicMock

    loader = ManifestIO(root_dir=jail_dir)
    target_file = jail_dir / "test.txt"
    target_file.write_text("content")

    real_stat = target_file.stat()

    bad_stat = MagicMock()
    bad_stat.st_ino = real_stat.st_ino + 1
    bad_stat.st_dev = real_stat.st_dev
    bad_stat.st_mode = real_stat.st_mode

    # We patch os.lstat and os.fstat in coreason_manifest.utils.io
    with patch("coreason_manifest.utils.io.os.lstat", return_value=real_stat) as mock_lstat:
        with patch("coreason_manifest.utils.io.os.fstat", return_value=bad_stat) as mock_fstat:
             with pytest.raises(SecurityViolationError, match="File swapped during open operation"):
                 loader.read_text("test.txt")
