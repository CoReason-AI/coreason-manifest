import re

with open("src/coreason_manifest/utils/algebra.py", "r") as f:
    content = f.read()

# Make the _apply_patch_replace return exact match without nested error prefixing
content = content.replace('raise ValueError(f"Cannot replace at path: {e}") from e', 'raise ValueError(f"{e}") from e')

with open("src/coreason_manifest/utils/algebra.py", "w") as f:
    f.write(content)
