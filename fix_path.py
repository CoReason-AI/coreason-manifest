import sys
import os

with open("tests/scripts/test_watchdog.py", "r") as f:
    content = f.read()

prefix = """import os
import sys

# Ensure the root directory is on the path so 'scripts' can be imported in CI
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

"""

content = prefix + content
with open("tests/scripts/test_watchdog.py", "w") as f:
    f.write(content)
