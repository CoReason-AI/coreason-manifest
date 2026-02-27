
import importlib.machinery
import importlib.util
import sys
import os
from pathlib import Path

def test_file_finder():
    os.makedirs("sandbox_test/pkg", exist_ok=True)
    with open("sandbox_test/pkg/__init__.py", "w") as f:
        f.write("x=1")
    with open("sandbox_test/mod.py", "w") as f:
        f.write("y=2")

    path = os.path.abspath("sandbox_test")

    loader_details = (importlib.machinery.SourceFileLoader, [".py"])
    finder = importlib.machinery.FileFinder(path, loader_details)

    print(f"Finder path: {path}")

    # Try finding 'mod'
    spec = finder.find_spec("mod")
    print(f"Spec for 'mod': {spec}")
    if spec:
        print(f"Origin: {spec.origin}")

    # Try finding 'pkg'
    spec_pkg = finder.find_spec("pkg")
    print(f"Spec for 'pkg': {spec_pkg}")
    if spec_pkg:
        print(f"Origin: {spec_pkg.origin}")

    # Clean up
    import shutil
    shutil.rmtree("sandbox_test")

if __name__ == "__main__":
    test_file_finder()
