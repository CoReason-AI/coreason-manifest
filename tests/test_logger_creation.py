# Prosperity-3.0
import subprocess
import sys
from pathlib import Path  # Ensure Path is available at module level for type hinting if needed


def test_logger_creates_directory(tmp_path: Path) -> None:
    """
    Verifies that the logger creates the 'logs' directory if it doesn't exist.
    We use a subprocess to ensure a fresh environment where the module hasn't been imported yet.
    """
    # Create a temporary script that imports the logger
    script_content = """
import sys
from pathlib import Path
import shutil

# Ensure logs dir does not exist initially
if Path("logs").exists():
    shutil.rmtree("logs")

from coreason_manifest.utils.logger import logger

# Check if logs dir was created
if Path("logs").exists():
    print("LOGS_CREATED")
else:
    print("LOGS_NOT_CREATED")
"""
    script_path = tmp_path / "check_logger.py"
    script_path.write_text(script_content)

    # Run the script
    from pathlib import Path  # Ensure Path is imported in test function scope or module scope

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=str(Path.cwd()),  # Run in repo root so it sees 'logs' relative to root
    )

    # Check output
    assert "LOGS_CREATED" in result.stdout
