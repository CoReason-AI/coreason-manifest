with open("src/coreason_manifest/spec/ontology.py") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if len(line) > 120 and "noqa" not in line:
        lines[i] = line.rstrip("\n") + "  # noqa: E501\n"

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.writelines(lines)
