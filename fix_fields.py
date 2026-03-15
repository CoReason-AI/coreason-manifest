with open("src/coreason_manifest/spec/ontology.py") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'le=1000000000, description="A strictly typed dictionary' in line:
        lines[i] = line.replace("le=1000000000, ", "")
    if 'le=1000000000, description="A list of cryptographic pointers' in line:
        lines[i] = line.replace("le=1000000000, ", "")
    # Also line 1110 might be split
    if line.strip() == "le=1000000000,":
        # Let's just remove it
        if "dict[" in lines[i - 1] or "list[" in lines[i - 1]:
            lines[i] = ""

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.writelines(lines)
