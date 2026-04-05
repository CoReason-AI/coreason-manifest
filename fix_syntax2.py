with open('src/coreason_manifest/spec/ontology.py', 'r') as f:
    content = f.read()

# The regex replacement broke `pattern="^[A-Za-z0-9+/]*={0,2}$"` because it matched the comma in `{0,2}`.
content = content.replace(
    'vector_base64: Annotated[str, StringConstraints(max_length=5000000, pattern="^[A-Za-z0-9+/]*={0)] = Field(2}$", description="The base64-encoded dense vector array.")',
    'vector_base64: Annotated[str, StringConstraints(max_length=5000000, pattern="^[A-Za-z0-9+/]*={0,2}$")] = Field(description="The base64-encoded dense vector array.")'
)

with open('src/coreason_manifest/spec/ontology.py', 'w') as f:
    f.write(content)
