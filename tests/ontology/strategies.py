# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Reusable Hypothesis strategies for the CoReason ontology test suite."""

import math
import string

from hypothesis import strategies as st


def node_cid_strategy() -> st.SearchStrategy[str]:
    """Generate valid NodeCIDState strings matching ^did:[a-z0-9]+:[a-zA-Z0-9.\\-_:]+$."""
    method = st.from_regex(r"[a-z0-9]{3,8}", fullmatch=True)
    specific = st.from_regex(r"[a-zA-Z0-9.\-_:]{3,20}", fullmatch=True)
    return st.builds(lambda m, s: f"did:{m}:{s}", method, specific)


def topology_hash_strategy() -> st.SearchStrategy[str]:
    """Generate valid TopologyHashReceipt strings matching ^[a-f0-9]{64}$."""
    return st.text(alphabet="0123456789abcdef", min_size=64, max_size=64)


def cid_strategy() -> st.SearchStrategy[str]:
    """Generate valid CID strings matching ^[a-zA-Z0-9_.:-]+$."""
    return st.text(
        alphabet=string.ascii_letters + string.digits + "_.:-",
        min_size=1,
        max_size=64,
    )


def ulid_strategy() -> st.SearchStrategy[str]:
    """Generate valid ULID strings matching ^[0-9A-HJKMNP-TV-Z]{26}$."""
    crockford = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    return st.text(alphabet=crockford, min_size=26, max_size=26)


def normalized_quaternion_strategy() -> st.SearchStrategy[tuple[float, float, float, float]]:
    """Generate quaternions normalized to magnitude ~1.0."""

    def normalize(components: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
        qx, qy, qz, qw = components
        mag = math.hypot(qx, qy, qz, qw)
        if mag < 1e-300:
            return (0.0, 0.0, 0.0, 1.0)
        return (qx / mag, qy / mag, qz / mag, qw / mag)

    return st.tuples(
        st.floats(min_value=-1.0, max_value=1.0),
        st.floats(min_value=-1.0, max_value=1.0),
        st.floats(min_value=-1.0, max_value=1.0),
        st.floats(min_value=-1.0, max_value=1.0),
    ).map(normalize)


def unit_vector_strategy() -> st.SearchStrategy[tuple[float, float, float]]:
    """Generate normalized 3D unit vectors."""

    def normalize(components: tuple[float, float, float]) -> tuple[float, float, float]:
        x, y, z = components
        mag = math.hypot(x, y, z)
        if mag == 0.0:
            return (1.0, 0.0, 0.0)
        return (x / mag, y / mag, z / mag)

    return st.tuples(
        st.floats(min_value=-1.0, max_value=1.0),
        st.floats(min_value=-1.0, max_value=1.0),
        st.floats(min_value=-1.0, max_value=1.0),
    ).map(normalize)


def se3_kwargs_strategy() -> st.SearchStrategy[dict]:  # type: ignore[type-arg]
    """Generate valid kwargs for SE3TransformProfile."""
    return st.fixed_dictionaries(
        {
            "reference_frame_cid": cid_strategy(),
            "x": st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
            "y": st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
            "z": st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        }
    )


def se3_full_kwargs_strategy() -> st.SearchStrategy[dict]:  # type: ignore[type-arg]
    """Generate valid kwargs for SE3TransformProfile with normalized quaternion."""

    def build(base: dict, quat: tuple[float, float, float, float]) -> dict:  # type: ignore[type-arg]
        return {**base, "qx": quat[0], "qy": quat[1], "qz": quat[2], "qw": quat[3]}

    return st.builds(build, se3_kwargs_strategy(), normalized_quaternion_strategy())
