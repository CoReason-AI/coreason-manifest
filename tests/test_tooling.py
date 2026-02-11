import sys
from unittest.mock import patch

import pytest
from _pytest.capture import CaptureFixture

from coreason_manifest.builder import AgentBuilder
from coreason_manifest.cli import main


def test_cli_validate_not_implemented(capsys: CaptureFixture[str]) -> None:
    """Test that the validate command prints a not implemented message."""
    test_args = ["coreason", "validate", "test.yaml"]
    with patch.object(sys, "argv", test_args):
        ret = main()
        assert ret == 1
        captured = capsys.readouterr()
        assert "Validation of test.yaml is not yet implemented" in captured.out


def test_cli_help(capsys: CaptureFixture[str]) -> None:
    """Test that help is printed when no command is given."""
    test_args = ["coreason"]
    with patch.object(sys, "argv", test_args):
        # argparse prints help and exits with 0 when no args if configured
        ret = main()
        assert ret == 0
        captured = capsys.readouterr()
        assert "usage: coreason" in captured.out


def test_builder_not_implemented() -> None:
    """Test that the AgentBuilder raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        AgentBuilder()
