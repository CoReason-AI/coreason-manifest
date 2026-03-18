import re

with open("src/coreason_manifest/utils/algebra.py", "r") as f:
    content = f.read()

# Fix the B904 issues which were caused by `raise ValueError` inside `except ValueError as e:` not using `from e`.
content = content.replace('raise ValueError(f"Invalid from_path operation: {e}")', 'raise ValueError(f"Invalid from_path operation: {e}") from e')
content = content.replace('raise ValueError(f"Cannot copy/move to path: {path}")', 'raise ValueError(f"Cannot copy/move to path: {path}") from e')
content = content.replace('raise ValueError(f"Index out of bounds: {path}")', 'raise ValueError(f"Index out of bounds: {path}") from e')
content = content.replace('raise ValueError(f"Cannot add to path: {path}")', 'raise ValueError(f"Cannot add to path: {path}") from e')

# Fix F841 unused variables
content = content.replace('patch_op = patch.op', '')
content = content.replace('patch_from = getattr(patch, "from_path", None)', '')

with open("src/coreason_manifest/utils/algebra.py", "w") as f:
    f.write(content)
