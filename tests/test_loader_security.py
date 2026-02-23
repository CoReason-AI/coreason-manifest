import errno
import os
import stat
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from coreason_manifest.utils.io import ManifestIO, SecurityViolationError


@pytest.fixture
def jail_dir(tmp_path: Path) -> Path:
    jail = tmp_path / "jail"
    jail.mkdir()
    return jail


def test_load_valid_file(jail_dir: Path) -> None:
    (jail_dir / "valid.yaml").write_text("key: value")
    loader = ManifestIO(root_dir=jail_dir, strict_security=False)
    data = loader.load("valid.yaml")
    assert data == {"key": "value"}


def test_path_traversal_detection(jail_dir: Path) -> None:
    # Create file outside jail
    outside = jail_dir.parent / "outside.yaml"
    outside.write_text("secret: data")

    loader = ManifestIO(root_dir=jail_dir, strict_security=False)

    # Try relative path traversal
    with pytest.raises(SecurityViolationError, match="Path Traversal Detected"):
        loader.load("../outside.yaml")

    # Try absolute path outside jail
    with pytest.raises(SecurityViolationError, match="Path Traversal Detected"):
        loader.load(str(outside.resolve()))


def test_posix_permissions(jail_dir: Path) -> None:
    unsafe_file = jail_dir / "unsafe.yaml"
    unsafe_file.write_text("danger: true")

    # Mock stats to simulate POSIX world-writable permissions
    mock_stat = MagicMock()
    mock_stat.st_mode = stat.S_IFREG | stat.S_IWOTH
    mock_stat.st_ino = 1
    mock_stat.st_dev = 1

    loader = ManifestIO(root_dir=jail_dir, strict_security=False)

    # We need to mock _is_posix to True, and lstat/fstat to return the unsafe mode
    # lstat and fstat must match to pass the TOCTOU check
    with (
        patch("coreason_manifest.utils.io.ManifestIO._is_posix", new_callable=PropertyMock) as mock_is_posix,
        patch("os.lstat", return_value=mock_stat),
        patch("os.fstat", return_value=mock_stat),
    ):
        mock_is_posix.return_value = True
        with pytest.raises(SecurityViolationError, match="Unsafe Permissions"):
            loader.load("unsafe.yaml")


def test_manifest_io_eloop_enoent() -> None:
    """Cover lines 60-63 in io.py: ELOOP and ENOENT handling."""
    import errno
    from unittest.mock import patch

    loader = ManifestIO(root_dir=Path("/tmp"), strict_security=False)

    # Mock os.lstat (new first check) AND os.open to ensure coverage
    with patch("os.lstat") as mock_lstat, patch("os.open") as mock_open:
        # 1. ELOOP (Simulate Loop)
        # Note: os.lstat typically doesn't raise ELOOP unless path components loop.
        # But if we want to test the ELOOP catch block around os.open, we need lstat to succeed.
        mock_lstat.return_value = os.stat_result((0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
        mock_open.side_effect = OSError(errno.ELOOP, "Too many symlinks")

        with pytest.raises(SecurityViolationError) as exc_sec:
            loader.read_text("loop.txt")
        assert "Symlink detected" in str(exc_sec.value)

    # 2. ENOENT (Missing File)
    # This will now be caught by os.lstat first
    with patch("os.lstat") as mock_lstat:
        mock_lstat.side_effect = OSError(errno.ENOENT, "No such file")
        with pytest.raises(FileNotFoundError):
            loader.read_text("missing.txt")

    # 3. EACCES (Permission Denied) - let lstat succeed, fail at open
    with patch("os.lstat") as mock_lstat, patch("os.open") as mock_open:
        mock_lstat.return_value = os.stat_result((0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
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


class TestManifestIOStrictSecurity:
    def test_strict_security_enforcement(self, tmp_path: Path) -> None:
        # Save original O_NOFOLLOW
        orig_nofollow = getattr(os, "O_NOFOLLOW", None)

        try:
            # Simulate missing O_NOFOLLOW
            if orig_nofollow is not None:
                delattr(os, "O_NOFOLLOW")

            # 1. Strict Mode: Should raise OSError (EnvironmentError)
            with pytest.raises(OSError, match="Host OS lacks O_NOFOLLOW support"):
                ManifestIO(tmp_path, strict_security=True)

            # 2. Permissive Mode: Should warn
            with pytest.warns(RuntimeWarning, match="TOCTOU protections disabled"):
                ManifestIO(tmp_path, strict_security=False)

        finally:
            # Restore O_NOFOLLOW
            if orig_nofollow is not None:
                os.O_NOFOLLOW = orig_nofollow  # type: ignore[misc]

    def test_init_with_nofollow_present(self, tmp_path: Path) -> None:
        """Cover the 'else' (implicit) branch of checking O_NOFOLLOW existence."""
        # Force O_NOFOLLOW to exist (simulating Linux on Windows)
        with patch.object(os, "O_NOFOLLOW", 0, create=True):
            # Should not raise or warn even with strict=True
            ManifestIO(tmp_path, strict_security=True)

    def test_toctou_race_detected_inode_mismatch(self, tmp_path: Path) -> None:
        """Test that mismatched inodes between lstat and fstat raises SecurityViolationError."""
        from typing import Any
        from unittest.mock import MagicMock, patch

        jail = tmp_path
        test_file = jail / "test.txt"
        test_file.touch()

        io = ManifestIO(jail, strict_security=False)

        # Prepare mocks
        stat_before = MagicMock()
        stat_before.st_ino = 12345
        stat_before.st_dev = 99
        stat_before.st_mode = stat.S_IFREG | 0o644

        stat_after = MagicMock()
        stat_after.st_ino = 67890  # Mismatch
        stat_after.st_dev = 99
        stat_after.st_mode = stat.S_IFREG | 0o644

        # We need to capture the real lstat for other files
        real_lstat = os.lstat

        def lstat_side_effect(path: str | Path, *args: Any, **kwargs: Any) -> Any:
            p = str(path)
            if p.endswith("test.txt"):
                return stat_before
            return real_lstat(path, *args, **kwargs)

        with (
            patch("os.lstat", side_effect=lstat_side_effect),
            patch("os.open", return_value=10),
            patch("os.fstat", return_value=stat_after),
            patch("os.fdopen"),
            patch("os.close") as mock_close,
        ):
            # Execute
            with pytest.raises(SecurityViolationError, match="File swapped during open operation"):
                io.read_text("test.txt")

            mock_close.assert_called_with(10)

    def test_toctou_race_detected_device_mismatch(self, tmp_path: Path) -> None:
        """Test that mismatched device IDs between lstat and fstat raises SecurityViolationError."""
        from typing import Any
        from unittest.mock import MagicMock, patch

        jail = tmp_path
        test_file = jail / "test.txt"
        test_file.touch()

        io = ManifestIO(jail, strict_security=False)

        # Prepare mocks
        stat_before = MagicMock()
        stat_before.st_ino = 12345
        stat_before.st_dev = 99
        stat_before.st_mode = stat.S_IFREG | 0o644

        stat_after = MagicMock()
        stat_after.st_ino = 12345
        stat_after.st_dev = 88  # Mismatch
        stat_after.st_mode = stat.S_IFREG | 0o644

        real_lstat = os.lstat

        def lstat_side_effect(path: str | Path, *args: Any, **kwargs: Any) -> Any:
            p = str(path)
            if p.endswith("test.txt"):
                return stat_before
            return real_lstat(path, *args, **kwargs)

        with (
            patch("os.lstat", side_effect=lstat_side_effect),
            patch("os.open", return_value=10),
            patch("os.fstat", return_value=stat_after),
            patch("os.fdopen"),
            patch("os.close") as mock_close,
        ):
            # Execute
            with pytest.raises(SecurityViolationError, match="File swapped during open operation"):
                io.read_text("test.txt")

            # Verify fd close was called
            mock_close.assert_called_with(10)

    def test_zero_inode_handling(self, tmp_path: Path) -> None:
        """Test that 0 inode triggers mtime/size check."""
        from typing import Any
        from unittest.mock import MagicMock, patch

        jail = tmp_path
        test_file = jail / "test.txt"
        test_file.touch()

        io = ManifestIO(jail, strict_security=False)

        # Prepare mocks
        stat_before = MagicMock()
        stat_before.st_ino = 0  # Trigger zero inode logic
        stat_before.st_mtime = 100
        stat_before.st_size = 50
        stat_before.st_mode = stat.S_IFREG | 0o644

        stat_after = MagicMock()
        stat_after.st_ino = 0
        stat_after.st_mtime = 101  # Mismatch
        stat_after.st_size = 50
        stat_after.st_mode = stat.S_IFREG | 0o644

        real_lstat = os.lstat

        def lstat_side_effect(path: str | Path, *args: Any, **kwargs: Any) -> Any:
            p = str(path)
            if p.endswith("test.txt"):
                return stat_before
            return real_lstat(path, *args, **kwargs)

        with (
            patch("os.lstat", side_effect=lstat_side_effect),
            patch("os.open", return_value=10),
            patch("os.fstat", return_value=stat_after),
            patch("os.fdopen"),
            patch("os.close") as mock_close,
            pytest.warns(RuntimeWarning, match="Inode heuristic blindspot"),
        ):
            with pytest.raises(SecurityViolationError, match="mtime/size mismatch"):
                io.read_text("test.txt")

            mock_close.assert_called_with(10)


class TestManifestIOCoverage:
    def test_symlink_loop_in_resolve(self, tmp_path: Path) -> None:
        """Cover line 90-92: RuntimeError('Symlink loop') in resolve."""
        io = ManifestIO(tmp_path, strict_security=False)

        # We need to mock Path.resolve.
        with (
            patch("pathlib.Path.resolve", side_effect=RuntimeError("Symlink loop")),
            pytest.raises(SecurityViolationError, match="Symlink detected during path resolution"),
        ):
            io.read_text("loop.txt")

    def test_symlink_loop_in_resolve_oserror(self, tmp_path: Path) -> None:
        """Cover OSError(ELOOP) in resolve."""
        io = ManifestIO(tmp_path, strict_security=False)

        with (
            patch("pathlib.Path.resolve", side_effect=OSError(errno.ELOOP, "Loop")),
            pytest.raises(SecurityViolationError, match="Symlink detected during path resolution"),
        ):
            io.read_text("loop.txt")

    def test_resolve_generic_oserror(self, tmp_path: Path) -> None:
        """Cover generic OSError in resolve."""
        io = ManifestIO(tmp_path, strict_security=False)

        with (
            patch("pathlib.Path.resolve", side_effect=OSError(errno.EACCES, "Permission denied")),
            pytest.raises(OSError, match="Permission denied") as exc,
        ):
            io.read_text("file.txt")
        assert exc.value.errno == errno.EACCES

    def test_lstat_generic_oserror(self, tmp_path: Path) -> None:
        """Cover line 105: lstat raises OSError != ENOENT."""
        io = ManifestIO(tmp_path, strict_security=False)

        # We must allow initial resolution calls to succeed if they use lstat
        # But here we want the lstat inside read_text (after resolution) to fail.
        # The resolution happens *before* the lstat call we want to test.
        # So we can just mock os.lstat globally if we assume resolution doesn't rely on it *inside* the function
        # (resolution happens before step 2).

        # However, ManifestIO.__init__ calls resolve(). And read_text calls resolve().
        # So we should construct ManifestIO first.

        with patch("os.lstat", side_effect=OSError(errno.EACCES, "Permission denied")):
            with pytest.raises(OSError, match="Permission denied") as exc:
                io.read_text("file.txt")
            assert exc.value.errno == errno.EACCES

    def test_open_generic_oserror(self, tmp_path: Path) -> None:
        """Cover line 118: open raises OSError != ELOOP != ENOENT."""
        io = ManifestIO(tmp_path, strict_security=False)
        test_file = tmp_path / "file.txt"
        test_file.touch()

        # We need lstat to succeed (real or mock) but open to fail.
        # Real lstat is fine.
        # We mock os.open.

        real_open = os.open

        def open_side_effect(path: str | Path, flags: int, *args: Any, **kwargs: Any) -> int:
            if str(path).endswith("file.txt"):
                raise OSError(errno.EACCES, "Permission denied")
            return real_open(path, flags, *args, **kwargs)

        with patch("os.open", side_effect=open_side_effect):
            with pytest.raises(OSError, match="Permission denied") as exc:
                io.read_text("file.txt")
            assert exc.value.errno == errno.EACCES

    def test_open_enoent_race_condition(self, tmp_path: Path) -> None:
        """Cover line 115-116: open raises ENOENT (file deleted after lstat)."""
        io = ManifestIO(tmp_path, strict_security=False)
        (tmp_path / "race.txt").touch()

        # Mock lstat to succeed, open to fail with ENOENT
        with (
            patch("os.lstat", return_value=os.stat_result((0, 0, 0, 0, 0, 0, 0, 0, 0, 0))),
            patch("os.open", side_effect=OSError(errno.ENOENT, "No such file")),
            pytest.raises(FileNotFoundError, match="File not found or inaccessible"),
        ):
            io.read_text("race.txt")

    def test_fdopen_failure_closes_fd(self, tmp_path: Path) -> None:
        """Cover line 165: os.close(fd) called when os.fdopen fails."""
        io = ManifestIO(tmp_path, strict_security=False)
        (tmp_path / "file.txt").touch()

        fd_val = 10

        # Mock lstat to return valid stat result
        stat_mock = MagicMock()
        stat_mock.st_ino = 1
        stat_mock.st_dev = 1
        stat_mock.st_mode = 0o644

        # We use side_effect for lstat to allow other calls if needed,
        # but here we can just return the mock.

        with (
            patch("os.lstat", return_value=stat_mock),
            patch("os.open", return_value=fd_val),
            patch("os.fstat", return_value=stat_mock),
            patch("os.fdopen", side_effect=Exception("fdopen failed")),
            patch("os.close") as mock_close,
        ):
            with pytest.raises(Exception, match="fdopen failed"):
                io.read_text("file.txt")

            mock_close.assert_called_with(fd_val)

    def test_load_invalid_yaml_structure(self, tmp_path: Path) -> None:
        """Cover line 166: content is not a dict."""
        io = ManifestIO(tmp_path, strict_security=False)
        (tmp_path / "list.yaml").write_text("- item1\n- item2")

        with pytest.raises(ValueError, match="Manifest content must be a dictionary"):
            io.load("list.yaml")

    def test_load_yaml_parse_error(self, tmp_path: Path) -> None:
        """Cover line 170: yaml.YAMLError."""
        io = ManifestIO(tmp_path, strict_security=False)
        # Tabs are not allowed in YAML and usually cause a ScannerError (subclass of YAMLError)
        (tmp_path / "bad.yaml").write_text("key: value\n\tbad_indent: value")

        with pytest.raises(ValueError, match="Failed to parse manifest file"):
            io.load("bad.yaml")
