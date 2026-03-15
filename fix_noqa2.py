with open("src/coreason_manifest/spec/ontology.py") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "TamperFaultEvent" in line and "class " in line:
        lines[i] = line.rstrip("\n") + "  # noqa: N818\n"

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.writelines(lines)
