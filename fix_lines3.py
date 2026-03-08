with open("src/coreason_manifest/state/semantic.py", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "The Content Identifier (CID) of the public evaluation key the orchestrator must utilize to perform privacy-preserving geometric math on ciphertext without epistemic contamination." in line:
        # replace with multi-line string correctly without regex issues
        # It looks like it's inside a list of strings due to textwrap from earlier?
        # Let's just do a simple replace on the file contents directly.
        pass

with open("src/coreason_manifest/state/semantic.py", "r") as f:
    content = f.read()

content = content.replace(
    '"The Content Identifier (CID) of the public evaluation key the orchestrator must utilize to perform privacy-preserving geometric math on ciphertext without epistemic contamination."',
    '(\n        "The Content Identifier (CID) of the public evaluation key the "\n        "orchestrator must utilize to perform privacy-preserving geometric "\n        "math on ciphertext without epistemic contamination."\n    )'
)

with open("src/coreason_manifest/state/semantic.py", "w") as f:
    f.write(content)
