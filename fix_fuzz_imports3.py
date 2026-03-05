with open("tests/test_fuzzing.py", "r") as f:
    lines = f.readlines()

import re

# Find definition
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if line.startswith("def draw_temporal_bounds"):
        start_idx = i - 1 # @st.composite
        end_idx = i + 17 # approx
        break

if start_idx != -1:
    func_lines = lines[start_idx:start_idx+20]
    # delete from original place
    del lines[start_idx:start_idx+20]

    # insert after imports
    for i, line in enumerate(lines):
        if line.startswith("any_node_adapter"):
            insert_idx = i
            break

    lines.insert(insert_idx, "".join(func_lines) + "\n")

with open("tests/test_fuzzing.py", "w") as f:
    f.writelines(lines)
