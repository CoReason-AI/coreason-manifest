import re

files_with_validators = [
    "src/coreason_manifest/workflow/topologies.py",
]

for file in files_with_validators:
    try:
        with open(file, "r") as f:
            content = f.read()

        replacement = 'if hasattr(self, "_cached_hash"):\n            object.__delattr__(self, "_cached_hash")\n        return self'
        content = re.sub(r'return self(?!.*\n\s*if hasattr)', replacement, content)

        with open(file, "w") as f:
            f.write(content)
    except FileNotFoundError:
        pass
