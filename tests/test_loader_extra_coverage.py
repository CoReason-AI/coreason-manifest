from pathlib import Path
from unittest.mock import patch

import pytest

from coreason_manifest.spec.interop.exceptions import SecurityJailViolationError
from coreason_manifest.utils.loader import load_flow_from_file


def test_load_flow_yaml_error(tmp_path: Path) -> None:
    f = tmp_path / "bad.yaml"
    # Unbalanced brackets are a sure way to cause YAMLError
    f.write_text("invalid: [")
    # strict_security=False because Windows does not support O_NOFOLLOW
    with pytest.raises(ValueError, match="Failed to parse manifest file"):
        load_flow_from_file(str(f), strict_security=False)


def test_load_flow_dynamic_exec_forbidden(tmp_path: Path) -> None:
    f = tmp_path / "flow.yaml"
    # Create a flow with a dynamic ref string
    # Ensure it's reachable in the structure
    content = """
kind: LinearFlow
metadata:
  name: A
  version: 1.0.0
  description: desc
steps:
  - id: step1
    node: "file.py:Node"  # This pattern triggers _scan_for_dynamic_references
"""
    f.write_text(content)

    # strict_security=False because Windows does not support O_NOFOLLOW
    with pytest.raises(SecurityJailViolationError, match="Dynamic code execution references detected"):
        load_flow_from_file(str(f), allow_dynamic_execution=False, strict_security=False)


def test_load_flow_relative_to_fail(tmp_path: Path) -> None:
    # Cover the ValueError in relative_to check
    # file at /tmp/file.yaml
    # root at /etc
    # ManifestIO mocked to succeed

    f = tmp_path / "file.yaml"
    f.write_text("kind: LinearFlow\nmetadata:\n  name: A\n  version: 1.0.0\n  description: d\nsequence: []")

    jail = tmp_path / "jail"
    jail.mkdir()

    with patch("coreason_manifest.utils.loader.ManifestIO") as mock_io:
        mock_io.return_value.read_text.return_value = f.read_text()

        # This forces file_path.relative_to(jail_root) to fail
        # strict_security=False passed implicitly? No, load_flow defaults to True.
        # But we mock ManifestIO so loader init args matter.
        # We should pass False here too for consistency, or mock the init.
        # But wait, we mock the CLASS.
        # So when load_flow calls ManifestIO(...), it gets the mock.
        # The mock doesn't run __init__ logic (OSError).
        # So we don't strictly need it here, but let's be safe.
        load_flow_from_file(str(f), root_dir=jail, strict_security=False)

        # Verify read_text called with name, confirming fallback
        mock_io.return_value.read_text.assert_called_with(f.name)
