import json
import subprocess
import sys
from pathlib import Path


def test_cli_validation_success(tmp_path: Path) -> None:
    """Proves exit code 0 on absolute topological match."""
    # Note: Requires a minimally valid JSON for DocumentLayoutAnalysis based on the schema
    valid_payload = tmp_path / "valid.json"
    valid_payload.write_text(json.dumps({"blocks": {}, "reading_order_edges": []}))

    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "coreason_manifest.cli.validate", "--step=step8_vision", str(valid_payload)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert not result.stderr


def test_cli_validation_failure(tmp_path: Path) -> None:
    """Proves exit code 1 and RFC 6902 stderr projection on violation."""
    invalid_payload = tmp_path / "invalid.json"
    invalid_payload.write_text(json.dumps({"invalid_key": "hallucination"}))

    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "coreason_manifest.cli.validate", "--step=step8_vision", str(invalid_payload)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "missing" in result.stderr or "extra_forbidden" in result.stderr


def test_cli_unknown_step() -> None:
    """Proves deterministic failure on unregistered schema bounds."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "coreason_manifest.cli.validate", "--step=hallucinated_step", "dummy.json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "FATAL: Unknown step" in result.stderr
