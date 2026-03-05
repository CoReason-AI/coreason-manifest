with open("tests/test_fuzzing.py", "r") as f:
    content = f.read()

dist_target = """@st.composite
def draw_distribution_profile(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "distribution_type": st.sampled_from(["gaussian", "uniform", "beta"]),
                "mean": st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False)),
                "variance": st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False)),
                "confidence_interval_95": st.one_of(
                    st.none(),
                    st.tuples(
                        st.floats(allow_nan=False, allow_infinity=False),
                        st.floats(allow_nan=False, allow_infinity=False),
                    ),
                ),
            }
        )
    )
    return res"""

dist_replacement = """@st.composite
def draw_distribution_profile(draw: Any) -> dict[str, Any]:
    distribution_type = draw(st.sampled_from(["gaussian", "uniform", "beta"]))
    mean = draw(st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False)))
    variance = draw(st.one_of(st.none(), st.floats(allow_nan=False, allow_infinity=False)))
    confidence_interval_95 = draw(
        st.one_of(
            st.none(),
            st.tuples(
                st.floats(allow_nan=False, allow_infinity=False),
                st.floats(allow_nan=False, allow_infinity=False),
            ),
        )
    )

    if confidence_interval_95 is not None:
        if confidence_interval_95[0] >= confidence_interval_95[1]:
            confidence_interval_95 = (confidence_interval_95[1], confidence_interval_95[0])
            if confidence_interval_95[0] >= confidence_interval_95[1]:
                # If they are exactly equal after swap, adjust one.
                confidence_interval_95 = (confidence_interval_95[0], confidence_interval_95[1] + 1.0)

    res: dict[str, Any] = {
        "distribution_type": distribution_type,
        "mean": mean,
        "variance": variance,
        "confidence_interval_95": confidence_interval_95,
    }
    return res"""

content = content.replace(dist_target, dist_replacement)

exec_target = """@st.composite
def draw_execution_span(draw: Any) -> dict[str, Any]:
    res: dict[str, Any] = draw(
        st.fixed_dictionaries(
            {
                "trace_id": st.text(min_size=1),
                "span_id": st.text(min_size=1),
                "parent_span_id": st.one_of(st.none(), st.text(min_size=1)),
                "name": st.text(min_size=1),
                "kind": st.sampled_from(["client", "server", "producer", "consumer", "internal"]),
                "start_time_unix_nano": st.integers(min_value=0),
                "end_time_unix_nano": st.one_of(st.none(), st.integers(min_value=0)),
                "status": st.sampled_from(["unset", "ok", "error"]),
                "events": st.lists(draw_span_event(), max_size=100),
            }
        )
    )
    return res"""

exec_replacement = """@st.composite
def draw_execution_span(draw: Any) -> dict[str, Any]:
    start_time_unix_nano = draw(st.integers(min_value=0))
    has_end_time = draw(st.booleans())
    end_time_unix_nano = None
    if has_end_time:
        delta = draw(st.integers(min_value=0))
        end_time_unix_nano = start_time_unix_nano + delta

    res: dict[str, Any] = {
        "trace_id": draw(st.text(min_size=1)),
        "span_id": draw(st.text(min_size=1)),
        "parent_span_id": draw(st.one_of(st.none(), st.text(min_size=1))),
        "name": draw(st.text(min_size=1)),
        "kind": draw(st.sampled_from(["client", "server", "producer", "consumer", "internal"])),
        "start_time_unix_nano": start_time_unix_nano,
        "end_time_unix_nano": end_time_unix_nano,
        "status": draw(st.sampled_from(["unset", "ok", "error"])),
        "events": draw(st.lists(draw_span_event(), max_size=100)),
    }
    return res"""

content = content.replace(exec_target, exec_replacement)

with open("tests/test_fuzzing.py", "w") as f:
    f.write(content)
