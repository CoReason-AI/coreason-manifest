import socket
import urllib.request
from pathlib import Path

import pytest

from coreason_manifest.utils.loader import SecurityViolationError, sandbox_context


def test_airgap_socket_connect(tmp_path: Path) -> None:
    jail_root = tmp_path / "jail"
    jail_root.mkdir()

    with sandbox_context(jail_root):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # This should be intercepted by the audit hook before any real connection is made
        with pytest.raises(SecurityViolationError, match=r"Network access blocked in sandbox: socket\.connect"):
            s.connect(("127.0.0.1", 80))


def test_airgap_urllib_request(tmp_path: Path) -> None:
    jail_root = tmp_path / "jail"
    jail_root.mkdir()

    with (
        sandbox_context(jail_root),
        pytest.raises(SecurityViolationError, match=r"Network access blocked in sandbox: urllib\.Request"),
    ):
        urllib.request.urlopen("http://127.0.0.1")
