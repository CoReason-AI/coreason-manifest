with open("tests/test_fuzzing.py", "r") as f:
    lines = f.readlines()

start_idx = -1
for i, line in enumerate(lines):
    if line.startswith("def draw_temporal_bounds"):
        start_idx = i - 1 # @st.composite
        break

if start_idx != -1:
    end_idx = start_idx + 1
    while end_idx < len(lines):
        if lines[end_idx].startswith("@st.composite") or lines[end_idx].startswith("def ") or lines[end_idx].startswith("any_topology_adapter"):
            break
        end_idx += 1

    func_lines = lines[start_idx:end_idx]
    del lines[start_idx:end_idx]

    insert_idx = -1
    for i, line in enumerate(lines):
        if "def test_anynode_routing" in line:
            insert_idx = i - 2
            break

    if insert_idx != -1:
        lines = lines[:insert_idx] + func_lines + ["\n"] + lines[insert_idx:]

with open("tests/test_fuzzing.py", "w") as f:
    f.writelines(lines)
