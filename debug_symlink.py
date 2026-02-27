import importlib.machinery
import importlib.util
import sys
import os
from pathlib import Path

def debug_symlink_traversal():
    base = Path("debug_symlink")
    if base.exists():
        import shutil
        shutil.rmtree(base)
    base.mkdir()

    jail = base / "jail"
    jail.mkdir()
    outside = base / "outside"
    outside.mkdir()

    # Create malicious symlink
    malicious_link = jail / "malicious_module"
    malicious_link.symlink_to(outside, target_is_directory=True)

    # Inside outside dir, we need something?
    # If malicious_module is a package, it needs __init__.py
    (outside / "__init__.py").touch()

    path = str(jail.resolve())
    loader_details = (importlib.machinery.SourceFileLoader, importlib.machinery.SOURCE_SUFFIXES)
    finder = importlib.machinery.FileFinder(path, loader_details)

    print(f"Jail: {path}")
    print(f"Symlink: {malicious_link} -> {malicious_link.resolve()}")

    try:
        spec = finder.find_spec("malicious_module")
        print(f"Spec found: {spec}")
        if spec:
            print(f"Origin: {spec.origin}")
            origin_path = Path(spec.origin).resolve()
            print(f"Resolved Origin: {origin_path}")
            print(f"Is relative to jail? {origin_path.is_relative_to(path)}")
    except Exception as e:
        print(f"Finder raised: {e}")

if __name__ == "__main__":
    debug_symlink_traversal()
