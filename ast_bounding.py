import re

with open('src/coreason_manifest/spec/ontology.py', 'r') as f:
    content = f.read()

# 1. Type Alias Overhaul
# type NodeIdentifierState = Annotated[str, Field(min_length=7, pattern="...")]
# becomes
# type NodeIdentifierState = Annotated[str, StringConstraints(min_length=7, pattern="..."), Field(description="...")]

aliases = ['NodeIdentifierState', 'ProfileIdentifierState', 'ToolIdentifierState', 'TopologyHashReceipt']

for alias in aliases:
    # We need to find the alias block and extract min_length, max_length, pattern, and description.
    # It's multiline.
    pattern = r'type ' + alias + r' = Annotated\[\s*str,\s*Field\(([\s\S]*?)\),\s*\]'
    match = re.search(pattern, content)
    if match:
        inner = match.group(1)
        # Parse arguments manually or via regex
        # Look for min_length, max_length, pattern, description, examples
        constraints = []
        field_args = []

        for kw in ['min_length', 'max_length', 'pattern']:
            kw_match = re.search(r'(' + kw + r'\s*=\s*(?:[^,]+|"[^"]+"))', inner)
            if kw_match:
                constraints.append(kw_match.group(1))

        for kw in ['description', 'examples']:
            kw_match = re.search(r'(' + kw + r'\s*=\s*\[[^\]]+\]|' + kw + r'\s*=\s*"[^"]+")', inner)
            if kw_match:
                field_args.append(kw_match.group(1))

        new_alias = f'type {alias} = Annotated[\n    str,\n    StringConstraints({", ".join(constraints)}),\n    Field({", ".join(field_args)}),\n]'
        content = content[:match.start()] + new_alias + content[match.end():]

# 2. Global String Sweep
# Convert EVERY str = Field(max_length=X, ...) to Annotated[str, StringConstraints(max_length=X)] = Field(...)
# Also str | None

# regex for: attr: str = Field(..., max_length=X, ...)
# or attr: str | None = Field(...)
def global_replace(match):
    full_match = match.group(0)
    attr_name = match.group(1)
    type_hint = match.group(2) # "str" or "str | None"
    field_content = match.group(3)

    # Check if there are constraints in field_content
    constraints = []

    # We remove constraints from field_content
    new_field_content = field_content
    for kw in ['min_length', 'max_length', 'pattern']:
        kw_match = re.search(r'\b' + kw + r'\s*=\s*([^,)]+)(?:\s*,\s*)?', new_field_content)
        if kw_match:
            val = kw_match.group(1)
            constraints.append(f"{kw}={val}")
            # remove from new_field_content
            new_field_content = new_field_content.replace(kw_match.group(0), "")

    # Cleanup trailing commas in new_field_content
    new_field_content = re.sub(r',\s*$', '', new_field_content.strip())
    new_field_content = re.sub(r',\s*,', ',', new_field_content)
    if new_field_content.startswith(','):
        new_field_content = new_field_content[1:].strip()

    if constraints:
        # Wrap the type
        constr_str = ", ".join(constraints)
        if type_hint.strip() == 'str':
            new_type = f'Annotated[str, StringConstraints({constr_str})]'
        else:
            new_type = f'Annotated[str, StringConstraints({constr_str})] | None'

        # If new_field_content is empty, just Field()
        if new_field_content:
            return f'{attr_name}: {new_type} = Field({new_field_content})'
        else:
            return f'{attr_name}: {new_type} = Field()'
    else:
        return full_match

# Find all occurrences of pattern: `name: str = Field(...)` or `name: str | None = Field(...)`
# Need to be careful about multiline Field(...)
# We'll use a regex that balances parentheses, but since python re doesn't support it, we'll iterate through lines or use a lazy match if it works.
# Field content might have nested commas but strings don't usually have unescaped parens here.
# Let's try matching until `)`

pattern_str = r'([A-Za-z0-9_]+):\s*(str|str\s*\|\s*None)\s*=\s*Field\(([\s\S]*?)\)'

content = re.sub(pattern_str, global_replace, content)

with open('src/coreason_manifest/spec/ontology.py', 'w') as f:
    f.write(content)
