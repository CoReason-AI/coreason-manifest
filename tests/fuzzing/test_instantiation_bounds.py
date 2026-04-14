# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from typing import Any

import hypothesis.strategies as st
import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    CognitiveSystemNodeProfile,
    ContextualizedSourceState,
    TopologicalFidelityReceipt,
)

valid_node_id_st = st.from_regex(r"^did:[a-z0-9]+:[a-zA-Z0-9.\-_:]+$", fullmatch=True)
node_st = st.builds(CognitiveSystemNodeProfile, description=st.text())


@st.composite
def three_nodes_st(draw: st.DrawFn) -> tuple[str, str, str, dict[str, Any]]:
    # We need exactly 3 distinct valid node IDs
    keys = draw(st.lists(valid_node_id_st, min_size=3, max_size=3, unique=True))
    nodes = {key: draw(node_st) for key in keys}
    return keys[0], keys[1], keys[2], nodes


def test_contextualized_source_entity_lengths() -> None:

    with pytest.raises(ValidationError):
        ContextualizedSourceState(
            target_string="x" * 100001,
            contextual_envelope=[],
            source_system_provenance_flag=False,
        )

    with pytest.raises(ValidationError):
        ContextualizedSourceState(
            target_string="Valid",
            contextual_envelope=["x"] * 10001,
            source_system_provenance_flag=False,
        )

    with pytest.raises(ValidationError):
        ContextualizedSourceState(
            target_string="Valid",
            contextual_envelope=["x" * 100001],
            source_system_provenance_flag=False,
        )


def test_data_fidelity_receipt_positive_token_density() -> None:

    with pytest.raises(ValidationError):
        TopologicalFidelityReceipt(
            contextual_completeness_score=1.0,
            surrounding_token_density=-1,
        )
