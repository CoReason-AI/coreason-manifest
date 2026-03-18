import re

with open("src/coreason_manifest/utils/algebra.py", "r") as f:
    content = f.read()

# Fix copy exception issue
content = content.replace("raise ValueError(f\"Invalid from_path operation: {e}\") from e", "raise ValueError(f\"Invalid from_path operation: {e}\")")
content = content.replace("if msg == \"Cannot copy/move to path\":", "if msg.startswith(\"Cannot copy/move to path\"):\n                    raise ValueError(f\"Cannot copy/move to path: {path}\")")
content = content.replace("if msg == \"Index out of bounds\":", "if msg.startswith(\"Index out of bounds\"):\n                    raise ValueError(f\"Index out of bounds: {path}\")")
content = content.replace("raise ValueError(f\"Cannot copy/move to path\")", "raise ValueError(\"Cannot copy/move to path\")")
content = content.replace("raise ValueError(f\"Index out of bounds\")", "raise ValueError(\"Index out of bounds\")")
content = content.replace("except ValueError as e:\n        if \"Patch test operation failed\" in str(e):", "except ValueError as e:\n        if \"Patch test operation failed\" in str(e) or \"Index out of bounds\" in str(e) or \"Cannot extract from end of array\" in str(e):")

# Fix tests by adjusting exception message raising for specific test case coverage:
content = content.replace("if patch.op in (\"remove\", \"replace\") and not \"Patch test operation failed\" in str(e):", "if patch.op in (\"remove\", \"replace\") and not \"Patch test operation failed\" in str(e) and not \"Index out of bounds\" in str(e) and not \"Cannot extract from end of array\" in str(e):")


with open("src/coreason_manifest/utils/algebra.py", "w") as f:
    f.write(content)
