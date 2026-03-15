# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any

import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, given, settings
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    BaseStateEvent,
    BrowserDOMState,
    DAGTopologyManifest,
    MultimodalTokenAnchorState,
    QuorumPolicy,
    SpatialBoundingBoxProfile,
    StateHydrationManifest,
    SystemNodeProfile,
    TaskAnnouncementIntent,
    TaxonomicRoutingPolicy,
)

valid_node_id_st = st.from_regex(r"^did:[a-z0-9]+:[a-zA-Z0-9.\-_:]+$", fullmatch=True)
node_st = st.builds(SystemNodeProfile, description=st.text())


@st.composite
def three_nodes_st(draw: st.DrawFn) -> tuple[str, str, str, dict[str, Any]]:
    # We need exactly 3 distinct valid node IDs
    keys = draw(st.lists(valid_node_id_st, min_size=3, max_size=3, unique=True))
    nodes = {key: draw(node_st) for key in keys}
    return keys[0], keys[1], keys[2], nodes


@given(data=three_nodes_st())
def test_dag_topology_explicit_cycle(data: tuple[str, str, str, dict[str, Any]]) -> None:
    """Topological Fuzzing: Generate directed edges for DAGTopologyManifest that explicitly
    contain cycles (A->B, B->C, C->A) when allow_cycles=False."""
    node_a, node_b, node_c, nodes = data

    with pytest.raises((ValidationError, ValueError)):
        DAGTopologyManifest(
            nodes=nodes,
            edges=[(node_a, node_b), (node_b, node_c), (node_c, node_a)],
            allow_cycles=False,
            max_depth=10,
            max_fan_out=10,
        )


@st.composite
def invalid_bbox_st(draw: st.DrawFn) -> tuple[float, float, float, float]:
    # x_min > x_max or y_min > y_max
    # Coordinates must be between 0.0 and 1.0
    x_min = draw(st.floats(min_value=0.0001, max_value=1.0))
    x_max = draw(st.floats(min_value=0.0, max_value=x_min - 0.00001))

    y_min = draw(st.floats(min_value=0.0, max_value=1.0))
    y_max = draw(st.floats(min_value=0.0, max_value=1.0))

    # Randomly swap invalidity to Y axis instead of X axis
    if draw(st.booleans()):
        x_min, x_max = x_max, x_min  # make X valid
        y_min = draw(st.floats(min_value=0.0001, max_value=1.0))
        y_max = draw(st.floats(min_value=0.0, max_value=y_min - 0.00001))

    return x_min, y_min, x_max, y_max


@given(coords=invalid_bbox_st())
def test_spatial_bounding_box_fuzzing(coords: tuple[float, float, float, float]) -> None:
    """Geometric/Spatial Fuzzing: Generate normalized coordinates for SpatialBoundingBoxProfile
    where minimums exceed maximums."""
    x_min, y_min, x_max, y_max = coords

    with pytest.raises((ValidationError, ValueError)):
        SpatialBoundingBoxProfile(x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max)


@given(coords=invalid_bbox_st())
def test_multimodal_token_anchor_state_fuzzing(coords: tuple[float, float, float, float]) -> None:
    """Geometric/Spatial Fuzzing: Generate normalized coordinates for MultimodalTokenAnchorState
    where minimums exceed maximums."""
    with pytest.raises((ValidationError, ValueError)):
        MultimodalTokenAnchorState(visual_patch_hashes=[], bounding_box=coords)


@st.composite
def invalid_quorum_st(draw: st.DrawFn) -> tuple[int, int]:
    # f >= 0, N > 0, N < 3f + 1
    f = draw(st.integers(min_value=1, max_value=100000))
    n = draw(st.integers(min_value=1, max_value=3 * f))
    return n, f


@given(params=invalid_quorum_st())
def test_byzantine_quorum_fuzzing(params: tuple[int, int]) -> None:
    """Byzantine Quorum Fuzzing: Generate integer configurations for QuorumPolicy
    where total nodes and tolerable faults violate N < 3f + 1."""
    n, f = params
    with pytest.raises((ValidationError, ValueError)):
        QuorumPolicy(
            max_tolerable_faults=f,
            min_quorum_size=n,
            state_validation_metric="ledger_hash",
            byzantine_action="quarantine",
        )


# SSRF fuzzing targets: local IPs, loopback, private networks, bogons
bogon_ips = [
    "127.0.0.1",
    "127.0.0.2",
    "127.1",
    "127.0.0.0",
    "0.0.0.0",  # noqa: S104
    "10.0.0.1",
    "10.1.2.3",
    "172.16.0.1",
    "172.31.255.255",
    "192.168.0.1",
    "192.168.1.1",
    "169.254.169.254",  # AWS metadata
    "224.0.0.1",  # Multicast
    "255.255.255.255",  # Broadcast
    "::1",
    "fe80::1",
    "fc00::1",
    "::ffff:127.0.0.1",
]

bogon_domains = [
    "localhost",
    "localhost.localdomain",
    "broadcasthost",
    "local",
    "internal",
    "something.local",
    "something.internal",
    "something.arpa",
    "127.0.0.1.nip.io",
    "10.0.0.1.sslip.io",
]

bogon_obfuscations = ["0x7f.0.0.1", "0x7f000001", "2130706433", "0177.0.0.1", "017700000001"]

all_ssrf_targets = bogon_ips + bogon_domains + bogon_obfuscations


@given(
    target=st.sampled_from(all_ssrf_targets),
    scheme=st.sampled_from(["http", "https", "ftp", "ws", "wss"]),
    port=st.one_of(st.none(), st.integers(min_value=1, max_value=65535)),
    path=st.text(alphabet="abcdefghijklmnopqrstuvwxyz/", min_size=0, max_size=20),
)
def test_semantic_ssrf_bounding_fuzzing(target: str, scheme: str, port: int | None, path: str) -> None:
    """Semantic SSRF Bounding: Generate obfuscated local IPs, Bogon spaces, and loopbacks
    and attempt to feed into BrowserDOMState."""
    port_str = f":{port}" if port else ""
    path_str = f"/{path}" if path and not path.startswith("/") else path

    if ":" in target and not target.startswith("[") and not target.startswith("0x"):
        target = f"[{target}]"
    url = f"{scheme}://{target}{port_str}{path_str}"

    with pytest.raises((ValidationError, ValueError)):
        BrowserDOMState(current_url=url, viewport_size=(800, 600), dom_hash="a" * 64, accessibility_tree_hash="a" * 64)


@st.composite
def deep_dict_st(draw: st.DrawFn) -> dict[str, Any]:
    depth = draw(st.integers(min_value=11, max_value=20))
    massive_string = "a" * 10001
    d: dict[str, Any] = {"leaf": massive_string}
    for _ in range(depth):
        d = {"nested": d}
    return d


@given(payload=deep_dict_st())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_payload_exhaustion_fuzzing(payload: dict[str, Any]) -> None:
    """Payload Exhaustion: Generate deeply recursive JSON structures to test _validate_payload_bounds
    limits via StateHydrationManifest."""
    with pytest.raises((ValidationError, ValueError)):
        StateHydrationManifest(
            epistemic_coordinate="test_coord",
            crystallized_ledger_cids=["a" * 64],
            working_context_variables=payload,
            max_retained_tokens=1000,
        )


@given(
    target_heuristic=st.text().filter(
        lambda x: x not in ["chronological", "entity_centric", "semantic_cluster", "confidence_decay"]
    )
)
def test_categorical_hallucination_fuzzing(target_heuristic: str) -> None:
    """Categorical Hallucination Fuzzing: Fuzz TaxonomyRoutingPolicy with invalid literal categories."""
    with pytest.raises((ValidationError, ValueError)):
        TaxonomicRoutingPolicy(
            policy_id="test",
            intent_to_heuristic_matrix={},
            fallback_heuristic=target_heuristic,  # type: ignore
        )


@given(massive_key=st.text(min_size=256))
def test_dictionary_bombing_fuzzing(massive_key: str) -> None:
    """Dictionary Bombing Fuzzing: Attempt to pass a massive key to intent_to_heuristic_matrix."""
    with pytest.raises((ValidationError, ValueError)):
        TaxonomicRoutingPolicy(
            policy_id="test",
            intent_to_heuristic_matrix={massive_key: "chronological"},
            fallback_heuristic="chronological",
        )


@given(timestamp=st.one_of(st.floats(max_value=-0.0001), st.floats(min_value=253402300799.1)))
def test_temporal_dilation_fuzzing(timestamp: float) -> None:
    with pytest.raises((ValidationError, ValueError)):
        BaseStateEvent(event_id="test_id", timestamp=timestamp)


@given(massive_id=st.text(min_size=129))
def test_id_bombing_fuzzing(massive_id: str) -> None:
    with pytest.raises((ValidationError, ValueError)):
        TaskAnnouncementIntent(task_id=massive_id, required_action_space_id=None, max_budget_magnitude=100)
