# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

"""Hypothesis property tests for uncovered branches in algebra.py projection and differential functions."""

from typing import Any

import hypothesis.strategies as st
import pytest
from hypothesis import given

from coreason_manifest.spec.ontology import (
    ActionSpaceManifest,
    AgentNodeProfile,
    BypassReceipt,
    DynamicRoutingManifest,
    EpistemicProvenanceReceipt,
    GlobalSemanticProfile,
    PeftAdapterContract,
    PermissionBoundaryPolicy,
    SideEffectProfile,
    StateDifferentialManifest,
    StateMutationIntent,
    SystemNodeProfile,
    ToolManifest,
    WorkflowManifest,
)
from coreason_manifest.utils.algebra import (
    apply_state_differential,
    calculate_agent_vram_footprint,
    compile_action_space_to_openai_tools,
    project_manifest_to_markdown,
    project_manifest_to_mermaid,
)


def _make_diff(patches: list[dict[str, Any]]) -> StateDifferentialManifest:
    """Helper to build a StateDifferentialManifest with required fields."""
    # Note: StateMutationIntent uses alias="from" for from_path
    intent_patches = [StateMutationIntent(**p) for p in patches]
    return StateDifferentialManifest(
        diff_id="diff_01",
        author_node_id="node_01",
        lamport_timestamp=1,
        vector_clock={"node_01": 1},
        patches=intent_patches,
    )


def test_mermaid_projection_with_bypassed_steps() -> None:
    """Prove project_manifest_to_mermaid covers bypassed_steps subgraph rendering."""
    bypass = BypassReceipt(
        artifact_event_id="artifact_01",
        bypassed_node_id="did:web:step_vision",
        justification="modality_mismatch",
        cryptographic_null_hash="a" * 64,
    )

    artifact_profile = GlobalSemanticProfile(
        artifact_event_id="artifact_01",
        detected_modalities=["text"],
        token_density=100,
    )

    manifest = DynamicRoutingManifest(
        manifest_id="manifest_01",
        artifact_profile=artifact_profile,
        active_subgraphs={"text": ["did:web:node_text_1"]},
        bypassed_steps=[bypass],
        branch_budgets_magnitude={},
    )

    mermaid_output = project_manifest_to_mermaid(manifest)

    assert "graph TD" in mermaid_output
    assert "Quarantined_Bypass" in mermaid_output
    assert "modality_mismatch" in mermaid_output
    assert "step_vision" in mermaid_output


def test_mermaid_projection_without_bypassed_steps() -> None:
    """Prove project_manifest_to_mermaid handles manifests without bypassed steps."""
    artifact_profile = GlobalSemanticProfile(
        artifact_event_id="artifact_01",
        detected_modalities=["text"],
        token_density=100,
    )

    manifest = DynamicRoutingManifest(
        manifest_id="manifest_02",
        artifact_profile=artifact_profile,
        active_subgraphs={"text": ["did:web:node_a", "did:web:node_b"]},
        bypassed_steps=[],
        branch_budgets_magnitude={},
    )

    mermaid_output = project_manifest_to_mermaid(manifest)

    assert "graph TD" in mermaid_output
    assert "Quarantined_Bypass" not in mermaid_output
    assert "node_a" in mermaid_output


def _build_dag_workflow() -> WorkflowManifest:
    """Helper to build a minimal DAGTopologyManifest-based WorkflowManifest."""
    from coreason_manifest.spec.ontology import DAGTopologyManifest

    nodes: dict[str, Any] = {
        "did:web:node_1": SystemNodeProfile(description="Agent node 1"),
    }

    topology = DAGTopologyManifest(
        nodes=nodes,
        edges=[],
        allow_cycles=False,
        max_depth=5,
        max_fan_out=3,
    )

    provenance = EpistemicProvenanceReceipt(
        extracted_by="did:web:genesis_node",
        source_event_id="evt_genesis",
    )

    return WorkflowManifest(
        genesis_provenance=provenance,
        manifest_version="1.0.0",
        topology=topology,
    )


def test_markdown_projection_basic() -> None:
    """Prove project_manifest_to_markdown covers node iteration path."""
    manifest = _build_dag_workflow()
    md = project_manifest_to_markdown(manifest)

    assert "# CoReason Agent Card" in md
    assert "## Workflow Identification" in md
    assert "dag" in md
    assert "Node: `did:web:node_1`" in md
    assert "Agent node 1" in md


def test_state_differential_copy_operation() -> None:
    """Prove apply_state_differential handles copy operations on dict targets."""
    manifest = _make_diff([{"op": "copy", "path": "/new_key", "from": "/source_key"}])

    state = {"source_key": "original_value", "other": "data"}
    result = apply_state_differential(state, manifest)

    assert result["new_key"] == "original_value"
    assert result["source_key"] == "original_value"


def test_state_differential_move_operation() -> None:
    """Prove apply_state_differential handles move operations removing from source."""
    manifest = _make_diff([{"op": "move", "path": "/destination", "from": "/source"}])

    state = {"source": "moving_value", "other": "stay"}
    result = apply_state_differential(state, manifest)

    assert result["destination"] == "moving_value"
    assert "source" not in result
    assert result["other"] == "stay"


def test_state_differential_copy_to_list() -> None:
    """Prove apply_state_differential handles copy operations targeting list indices."""
    manifest = _make_diff([{"op": "copy", "path": "/items/1", "from": "/source"}])

    state = {"source": "copied_val", "items": ["a", "b", "c"]}
    result = apply_state_differential(state, manifest)

    assert result["items"] == ["a", "copied_val", "b", "c"]


def test_state_differential_move_within_list() -> None:
    """Prove apply_state_differential handles move within same list."""
    manifest = _make_diff([{"op": "move", "path": "/items/2", "from": "/items/0"}])

    state = {"items": ["first", "second", "third"]}
    result = apply_state_differential(state, manifest)

    assert "first" in result["items"]


def test_state_differential_copy_to_list_end() -> None:
    """Prove apply_state_differential handles copy to end of list with '-' token."""
    manifest = _make_diff([{"op": "copy", "path": "/items/-", "from": "/source"}])

    state = {"source": "appended_val", "items": ["a", "b"]}
    result = apply_state_differential(state, manifest)

    assert result["items"] == ["a", "b", "appended_val"]


def test_state_differential_replace_at_array_end_rejected() -> None:
    """Prove apply_state_differential rejects replace at '-' (array end marker)."""
    manifest = _make_diff([{"op": "replace", "path": "/items/-", "value": "new_val"}])

    state = {"items": ["a", "b"]}
    with pytest.raises(ValueError, match="Cannot replace"):
        apply_state_differential(state, manifest)


def test_state_differential_from_path_list_traversal() -> None:
    """Prove apply_state_differential resolves from_path through list indices."""
    manifest = _make_diff([{"op": "copy", "path": "/destination", "from": "/items/1"}])

    state = {"items": ["zero", "one", "two"], "destination": "old"}
    result = apply_state_differential(state, manifest)

    assert result["destination"] == "one"


def test_state_differential_copy_move_prefix_rejection() -> None:
    """Prove that copy/move rejects from_path being a proper prefix of path."""
    manifest = _make_diff([{"op": "move", "path": "/a/b/c", "from": "/a/b"}])

    state = {"a": {"b": {"c": "val", "d": "other"}}}
    with pytest.raises(ValueError, match="proper prefix"):
        apply_state_differential(state, manifest)


def test_state_differential_from_path_missing() -> None:
    """Prove copy/move rejects None from_path."""
    manifest = _make_diff([{"op": "copy", "path": "/target"}])

    state = {"target": "val"}
    with pytest.raises(ValueError, match="mathematically required"):
        apply_state_differential(state, manifest)


def test_state_differential_non_traversable_target() -> None:
    """Prove apply_state_differential rejects paths through non-dict/list intermediate nodes."""
    manifest = _make_diff([{"op": "add", "path": "/scalar/child", "value": "new"}])

    state = {"scalar": "plain_string"}
    with pytest.raises(ValueError, match=r"Cannot add to path|Invalid path"):
        apply_state_differential(state, manifest)


tool_st = st.builds(
    ToolManifest,
    tool_name=st.from_regex(r"^[a-zA-Z0-9_-]+$", fullmatch=True).filter(lambda x: 1 <= len(x) <= 128),
    description=st.text(min_size=1, max_size=100),
    input_schema=st.just({"type": "object", "properties": {"arg": {"type": "string"}}}),
    side_effects=st.builds(SideEffectProfile, is_idempotent=st.booleans(), mutates_state=st.booleans()),
    permissions=st.builds(
        PermissionBoundaryPolicy,
        network_access=st.booleans(),
        file_system_mutation_forbidden=st.booleans(),
        allowed_domains=st.none(),
        auth_requirements=st.none(),
    ),
    sla=st.none(),
    is_preemptible=st.booleans(),
)


@given(st.lists(tool_st, min_size=0, max_size=10, unique_by=lambda x: x.tool_name))
def test_compile_action_space_to_openai_tools(tools: list[ToolManifest]) -> None:
    """Prove compile_action_space_to_openai_tools maps native_tools correctly."""
    manifest = ActionSpaceManifest(
        action_space_id="test_space",
        native_tools=tools,
    )
    result = compile_action_space_to_openai_tools(manifest)

    # native_tools in ActionSpaceManifest gets sorted by tool_name, so we sort our list too
    sorted_tools = sorted(tools, key=lambda x: x.tool_name)

    assert len(result) == len(sorted_tools)
    for i, tool in enumerate(sorted_tools):
        assert result[i]["type"] == "function"
        assert result[i]["function"]["name"] == tool.tool_name
        assert result[i]["function"]["description"] == tool.description
        assert result[i]["function"]["parameters"] == tool.input_schema


@given(st.lists(st.integers(min_value=1, max_value=1000000000), min_size=0, max_size=10))
def test_calculate_agent_vram_footprint(vram_sizes: list[int]) -> None:
    """Prove calculate_agent_vram_footprint perfectly matches sum() of vram_footprint_bytes."""
    adapters = []
    for i, size in enumerate(vram_sizes):
        # We must use setattr to bypass the frozen=True restriction of CoreasonBaseState
        # because PeftAdapterContract no longer defines vram_footprint_bytes in ontology.
        # But calculate_agent_vram_footprint uses getattr(adapter, "vram_footprint_bytes", 0).
        adapter = PeftAdapterContract(
            adapter_id=f"adapter_{i}",
            safetensors_hash="a" * 64,
            base_model_hash="b" * 64,
            adapter_rank=8,
            target_modules=["q_proj", "v_proj"],
        )
        object.__setattr__(adapter, "vram_footprint_bytes", size)
        adapters.append(adapter)

    agent = AgentNodeProfile(
        description="test agent",
        type="agent",
        peft_adapters=adapters,
    )

    result = calculate_agent_vram_footprint(agent)
    assert result == sum(vram_sizes)
