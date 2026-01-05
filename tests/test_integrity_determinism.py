# Prosperity-3.0
import hashlib
from pathlib import Path

from coreason_manifest.integrity import IntegrityChecker


def test_cross_platform_sorting_determinism(tmp_path: Path) -> None:
    """
    Verify that files are sorted by their POSIX path string (ASCII order),
    ensuring 'B.txt' comes before 'a.txt' even on Windows.
    """
    src = tmp_path / "src"
    src.mkdir()

    # Create files 'a.txt' and 'B.txt'
    # ASCII: 'B' (66) < 'a' (97)
    (src / "a.txt").write_text("content")
    (src / "B.txt").write_text("content")

    # Calculate hash
    actual_hash = IntegrityChecker.calculate_hash(src)

    # Manually calculate expected hash using strict ASCII order
    sha256 = hashlib.sha256()

    # Order must be B.txt, then a.txt
    sorted_files = ["B.txt", "a.txt"]

    for fname in sorted_files:
        # Update with relative path
        sha256.update(fname.encode("utf-8"))
        # Update with content
        sha256.update(b"content")

    expected_hash = sha256.hexdigest()

    assert actual_hash == expected_hash, (
        "Hash calculation must use ASCII sorting order (B < a) for cross-platform determinism"
    )
