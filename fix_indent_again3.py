with open("src/coreason_manifest/spec/ontology.py", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for l in lines:
    if l.startswith('    @model_validator(mode="after")') and new_lines[-1].strip() == "]":
        skip = True

    if skip:
        if l.strip() == "return self":
            skip = False
        continue

    new_lines.append(l)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write("".join(new_lines))
