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
        if lines[end_idx].startswith("@st.composite") or lines[end_idx].startswith("def ") or lines[end_idx].startswith("@given") or lines[end_idx].startswith("any_"):
            break
        end_idx += 1

    func_lines = lines[start_idx:end_idx]
    del lines[start_idx:end_idx]

    # Let's insert it before line 500, wait, it says at 540 "temporal_bounds" is used.
    # Where does that block start?

    insert_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("def test_semanticnode_fuzzing"):
            # find @given above it
            for j in range(i, -1, -1):
                if lines[j].startswith("@given"):
                    insert_idx = j
                    break
            break

    if insert_idx != -1:
        lines = lines[:insert_idx] + ["\n"] + func_lines + ["\n"] + lines[insert_idx:]

with open("tests/test_fuzzing.py", "w") as f:
    f.writelines(lines)
