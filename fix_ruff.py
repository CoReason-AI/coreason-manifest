with open("src/coreason_manifest/spec/ontology.py") as f:
    content = f.read()

content = content.replace(
    '        description="A strictly typed dictionary for ephemeral context variables injected at runtime. AGENT INSTRUCTION: This matrix is deterministically sorted by CoreasonBaseState natively."\n',
    '        description="A strictly typed dictionary for ephemeral context variables injected at runtime. AGENT INSTRUCTION: This matrix is deterministically sorted by CoreasonBaseState natively."  # noqa: E501\n'
)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)
