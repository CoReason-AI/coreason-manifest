import re

with open("src/coreason_manifest/state/semantic.py", "r") as f:
    content = f.read()

# public_key_id is currently:
# public_key_id: str = Field(description="The Content Identifier (CID) of the public evaluation key the orchestrator must utilize to perform privacy-preserving geometric math on ciphertext without epistemic contamination.")
# that exceeds 120 char length

desc = (
    '(\n'
    '        "The Content Identifier (CID) of the public evaluation key the orchestrator "\n'
    '        "must utilize to perform privacy-preserving geometric math on ciphertext "\n'
    '        "without epistemic contamination."\n'
    '    )'
)
content = re.sub(
    r'description="The Content Identifier \(CID\) of the public evaluation key the orchestrator must utilize to perform privacy-preserving geometric math on ciphertext without epistemic contamination\."',
    f'description={desc}',
    content
)

with open("src/coreason_manifest/state/semantic.py", "w") as f:
    f.write(content)
