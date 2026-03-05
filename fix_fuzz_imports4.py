with open("tests/test_fuzzing.py", "r") as f:
    lines = f.readlines()

start_idx = -1
for i, line in enumerate(lines):
    if line.startswith("def draw_temporal_bounds"):
        start_idx = i - 1 # @st.composite
        break

if start_idx != -1:
    end_idx = start_idx
    while end_idx < len(lines):
        end_idx += 1
        if end_idx < len(lines) and lines[end_idx].startswith("@st.composite"):
            break

    func_lines = lines[start_idx:end_idx]
    del lines[start_idx:end_idx]

    insert_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("any_node_adapter"):
            insert_idx = i
            break

    if insert_idx != -1:
        lines = lines[:insert_idx] + func_lines + ["\n"] + lines[insert_idx:]

with open("tests/test_fuzzing.py", "w") as f:
    f.writelines(lines)
