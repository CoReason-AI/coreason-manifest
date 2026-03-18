import re

with open("src/coreason_manifest/utils/algebra.py", "r") as f:
    content = f.read()

# Fix the B904 issues which were caused by `raise ValueError` inside `except ValueError as e:` not using `from e`.
content = content.replace('raise ValueError("Invalid from_path operation: {e}")', 'raise ValueError(f"Invalid from_path operation: {e}") from e')

with open("src/coreason_manifest/utils/algebra.py", "w") as f:
    f.write(content)
