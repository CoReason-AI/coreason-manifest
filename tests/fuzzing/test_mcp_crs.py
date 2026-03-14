# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Literal

import hypothesis.strategies as st
from hypothesis import given

from coreason_manifest.spec.mcp_tools import (
    QueryLineageGraphRequest,
    QueryLineageGraphResponse,
    SummarizeEpistemicReceiptRequest,
)


@given(
    target_merkle_root=st.from_regex(r"^[a-fA-F0-9]{64}$", fullmatch=True),
    max_depth=st.integers(min_value=1, max_value=50)
)
def test_fuzz_query_lineage_graph_request(target_merkle_root: str, max_depth: int) -> None:
    req = QueryLineageGraphRequest(
        target_merkle_root=target_merkle_root,
        max_depth=max_depth
    )
    # Ensure properties are bound properly
    assert req.type == "request"
    assert 1 <= req.max_depth <= 50
    assert len(req.target_merkle_root) == 64


@given(
    target_merkle_root=st.from_regex(r"^[a-fA-F0-9]{64}$", fullmatch=True),
    max_depth=st.integers(min_value=1, max_value=50)
)
def test_mcp_query_request(target_merkle_root: str, max_depth: int) -> None:
    req = QueryLineageGraphRequest(
        target_merkle_root=target_merkle_root,
        max_depth=max_depth
    )
    assert req.type == "request"


@given(
    receipt_cid=st.text(min_size=1),
    summary_format=st.sampled_from(["natural_language", "structured_json", "markdown_table"])
)
def test_fuzz_summarize_epistemic_receipt_request(
    receipt_cid: str,
    summary_format: Literal["natural_language", "structured_json", "markdown_table"]
) -> None:
    req = SummarizeEpistemicReceiptRequest(
        receipt_cid=receipt_cid,
        summary_format=summary_format
    )
    assert req.type == "request"
    assert len(req.receipt_cid) >= 1
    assert req.summary_format in ["natural_language", "structured_json", "markdown_table"]


def test_mcp_query_response_sorting() -> None:
    # Test array sorting rules explicitly
    root = "a" * 64

    node1 = "did:example:node_b"
    node2 = "did:example:node_a"
    node3 = "did:example:node_c"

    nodes = [node1, node2, node3]
    resp = QueryLineageGraphResponse(queried_merkle_root=root, discovered_nodes=nodes)

    assert resp.discovered_nodes == ["did:example:node_a", "did:example:node_b", "did:example:node_c"]
