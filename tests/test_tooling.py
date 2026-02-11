import pytest
from coreason_manifest.cli import main
from coreason_manifest.builder import AgentBuilder

def test_cli_validate_not_implemented(capsys):
    """Test that the validate command prints a not implemented message."""
    # Simulate arguments
    import sys
    from unittest.mock import patch

    test_args = ["coreason", "validate", "test.yaml"]
    with patch.object(sys, 'argv', test_args):
        ret = main()
        assert ret == 1
        captured = capsys.readouterr()
        assert "Validation of test.yaml is not yet implemented" in captured.out

def test_cli_help(capsys):
    """Test that help is printed when no command is given."""
    import sys
    from unittest.mock import patch

    test_args = ["coreason"]
    with patch.object(sys, 'argv', test_args):
        # argparse prints help and exits with 0 when no args if configured,
        # but here we handled it manually or via argparse behavior.
        # Wait, my cli.py implementation:
        # parser.parse_args() will return empty namespace if no args? No, subparsers usually required=False by default in recent py?
        # Let's check cli.py logic.
        # if args.command == "validate": ...
        # parser.print_help()
        # return 0

        ret = main()
        assert ret == 0
        captured = capsys.readouterr()
        assert "usage: coreason" in captured.out

def test_builder_not_implemented():
    """Test that the AgentBuilder raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        AgentBuilder()
