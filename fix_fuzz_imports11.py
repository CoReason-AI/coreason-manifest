with open("tests/test_fuzzing.py", "r") as f:
    lines = f.readlines()

func_def = """@st.composite
def draw_temporal_bounds(draw: Any) -> dict[str, Any]:
    valid_from = draw(st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False)))
    valid_to = None
    if valid_from is not None:
        delta = draw(st.floats(min_value=0.0, allow_nan=False, allow_infinity=False))
        valid_to = valid_from + delta
    else:
        valid_to = draw(st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False)))

    return {
        "valid_from": valid_from,
        "valid_to": valid_to,
        "interval_type": draw(st.one_of(
            st.none(),
            st.sampled_from(["strictly_precedes", "overlaps", "contains", "causes", "mitigates"]),
        )),
    }
"""

insert_idx = -1
for i, line in enumerate(lines):
    if line.startswith("def test_semanticnode_fuzzing"):
        for j in range(i, -1, -1):
            if lines[j].startswith("@given"):
                insert_idx = j
                break
        break

if insert_idx != -1:
    lines.insert(insert_idx, func_def + "\n")

with open("tests/test_fuzzing.py", "w") as f:
    f.writelines(lines)
