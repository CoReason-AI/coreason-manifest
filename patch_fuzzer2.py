import re

with open("tests/test_fuzzing.py", "r") as f:
    content = f.read()

# Fix the temporal bounds logic
temporal_target = """            "temporal_bounds": st.one_of(
                st.none(),
                st.fixed_dictionaries(
                    {
                        "valid_from": st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False)),
                        "valid_to": st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False)),
                        "interval_type": st.one_of(
                            st.none(),
                            st.sampled_from(["strictly_precedes", "overlaps", "contains", "causes", "mitigates"]),
                        ),
                    }
                ),
            ),"""

temporal_replacement = """            "temporal_bounds": st.one_of(
                st.none(),
                draw_temporal_bounds()
            ),"""

content = content.replace(temporal_target, temporal_replacement)

draw_temporal_bounds_str = """
@st.composite
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

if "def draw_temporal_bounds" not in content:
    content = content.replace("@st.composite\ndef draw_salience_profile", draw_temporal_bounds_str + "\n\n@st.composite\ndef draw_salience_profile")

with open("tests/test_fuzzing.py", "w") as f:
    f.write(content)
