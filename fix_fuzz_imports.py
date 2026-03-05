import re

with open("tests/test_fuzzing.py", "r") as f:
    content = f.read()

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

content = content.replace(func_def, "")
# Find first @st.composite
content = content.replace("@st.composite\ndef draw_any_tool", func_def + "\n@st.composite\ndef draw_any_tool")

with open("tests/test_fuzzing.py", "w") as f:
    f.write(content)
