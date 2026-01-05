import shutil

import pytest


@pytest.fixture(autouse=True)
def mock_shutil_which(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Mock shutil.which to always return a fake path for 'opa',
    unless the test specifically needs strict behavior.
    """
    original_which = shutil.which

    import os
    from typing import Optional

    def side_effect(cmd: str, mode: int = os.F_OK | os.X_OK, path: Optional[str] = None) -> Optional[str]:
        if cmd == "opa":
            return "/usr/bin/mock_opa"
        return original_which(cmd, mode, path)

    monkeypatch.setattr(shutil, "which", side_effect)
