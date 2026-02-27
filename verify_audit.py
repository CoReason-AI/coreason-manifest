import shutil
import sys
from pathlib import Path

from coreason_manifest.utils.loader import SecurityViolationError, sandbox_context


def verify_audit_hook() -> None:
    base = Path("verify_audit")
    if base.exists():
        shutil.rmtree(base)
    base.mkdir()

    jail = base / "jail"
    jail.mkdir()

    outside = base / "outside.txt"
    outside.write_text("secret")

    # 1. Test allowed access (inside jail)
    (jail / "inside.txt").write_text("ok")

    print("Testing allowed file access...")
    with sandbox_context(jail):
        with open(jail / "inside.txt") as f:
            content = f.read()
        assert content == "ok"
    print("Allowed access passed.")

    # 2. Test disallowed access (outside jail)
    print("Testing disallowed file access...")
    try:
        with sandbox_context(jail), open(outside) as f:
            content = f.read()
        print("ERROR: Disallowed access check FAILED. Should have raised SecurityViolationError.")
        sys.exit(1)
    except SecurityViolationError as e:
        print(f"Disallowed access check passed: {e}")
    except OSError as e:
        # Sometimes audit hook raises OSError (Permission denied) if sys.addaudithook implementation does so?
        # But we raise SecurityViolationError.
        print(f"Caught unexpected OSError: {e}")
        sys.exit(1)

    # 3. Test python runtime access (should be allowed)
    print("Testing python runtime access...")
    try:
        with sandbox_context(jail):
            import os

            # accessing __file__ of os module
            with open(os.__file__) as f:
                pass
        print("Python runtime access passed.")
    except Exception as e:
        print(f"ERROR: Python runtime access failed: {e}")
        sys.exit(1)

    print("All audit verification checks passed.")
    shutil.rmtree(base)


if __name__ == "__main__":
    verify_audit_hook()
