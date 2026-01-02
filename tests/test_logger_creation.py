# Prosperity-3.0
import os
import subprocess
import sys
from pathlib import Path


def test_logger_creates_directory(tmp_path: Path) -> None:
    """
    Verifies that the logger creates the logs directory if it doesn't exist.
    We use a custom env var to point to a non-existent directory.
    """
    custom_log_dir = tmp_path / "custom_logs"

    script_content = """
import sys
from pathlib import Path
from coreason_manifest.utils.logger import logger

# Check if the custom log dir was created
log_dir = Path(sys.argv[1])
if log_dir.exists():
    print("LOGS_CREATED")
else:
    print("LOGS_NOT_CREATED")
"""
    script_path = tmp_path / "check_logger.py"
    script_path.write_text(script_content)

    # Run the script with the env var set
    env = os.environ.copy()
    env["COREASON_LOG_DIR"] = str(custom_log_dir)

    result = subprocess.run(
        [sys.executable, str(script_path), str(custom_log_dir)],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(Path.cwd()),
    )

    if "LOGS_CREATED" not in result.stdout:
        print("Subprocess stdout:", result.stdout)
        print("Subprocess stderr:", result.stderr)

    assert "LOGS_CREATED" in result.stdout
