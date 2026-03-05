with open("tests/test_fuzzing.py", "r") as f:
    lines = f.readlines()

start_idx = -1
for i, line in enumerate(lines):
    if line.startswith("def draw_temporal_bounds"):
        start_idx = i - 1 if lines[i-1].startswith("@st.composite") else i
        break

if start_idx != -1:
    end_idx = start_idx + 1
    while end_idx < len(lines):
        if lines[end_idx].startswith("@st.composite") or lines[end_idx].startswith("def ") or lines[end_idx].startswith("@given"):
            break
        end_idx += 1

    func_lines = lines[start_idx:end_idx]
    del lines[start_idx:end_idx]

    insert_idx = -1
    for i, line in enumerate(lines):
        if "test_semanticnode_fuzzing" in line:
            # We must put draw_temporal_bounds BEFORE the @given for test_semanticnode_fuzzing
            # Actually we can just put it at line 50. Let's find first @given
            pass

    for i, line in enumerate(lines):
        if line.startswith("@st.composite"):
            insert_idx = i
            break

    if insert_idx != -1:
        lines = lines[:insert_idx] + func_lines + ["\n"] + lines[insert_idx:]

with open("tests/test_fuzzing.py", "w") as f:
    f.writelines(lines)
