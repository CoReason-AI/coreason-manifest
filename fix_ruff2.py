with open('src/coreason_manifest/spec/ontology.py', 'r') as f:
    lines = f.readlines()

in_tom = False
sort_arrays_count = 0

out_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if "class TheoryOfMindSnapshot(" in line:
        in_tom = True
    elif "class " in line and line.startswith("class ") and "TheoryOfMindSnapshot" not in line:
        in_tom = False

    if in_tom and "@model_validator(mode=\"after\")" in line:
        if i+1 < len(lines) and "def sort_arrays" in lines[i+1]:
            sort_arrays_count += 1
            if sort_arrays_count > 1:
                # skip this method
                i += 5
                continue

    out_lines.append(line)
    i += 1

with open('src/coreason_manifest/spec/ontology.py', 'w') as f:
    f.write(''.join(out_lines))
