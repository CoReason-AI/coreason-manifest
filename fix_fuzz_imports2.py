with open("tests/test_fuzzing.py", "r") as f:
    content = f.read()

import re
# Ensure draw_temporal_bounds is defined earlier.
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

if "def draw_temporal_bounds" not in content[:5000]: # It's probably at the end or removed
    # Just insert it after imports
    import_end = content.find("any_node_adapter")
    content = content[:import_end] + func_def + "\n" + content[import_end:]

with open("tests/test_fuzzing.py", "w") as f:
    f.write(content)
