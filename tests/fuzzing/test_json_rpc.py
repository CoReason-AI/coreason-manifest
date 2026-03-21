# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import typing

import hypothesis.strategies as st
import pytest
from hypothesis import given
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    ActionSpaceManifest,
    BoundedJSONRPCIntent,
    ContinuousMutationPolicy,
    EpistemicLedgerState,
    LatentSchemaInferenceIntent,
    LatentScratchpadReceipt,
    MarketContract,
    PermissionBoundaryPolicy,
    SideEffectProfile,
    ThoughtBranchState,
    ToolManifest,
)

# Define a recursive strategy to simulate valid JSON payload topologies
valid_json_st = st.recursive(
    st.none() | st.booleans() | st.floats(allow_nan=False, allow_infinity=False) | st.integers() | st.text(max_size=50),
    lambda children: st.lists(children, max_size=5) | st.dictionaries(st.text(max_size=50), children, max_size=5),
    max_leaves=10,
)


@given(params=st.one_of(st.none(), st.dictionaries(st.text(max_size=50), valid_json_st, max_size=5)))
def test_valid_json_rpc_intent(params: typing.Any) -> None:
    # Prove that payloads under the depth limits are instantiated without error
    intent = BoundedJSONRPCIntent(jsonrpc="2.0", method="fuzzed_method", params=params, id=1)
    assert intent.params == params


@given(
    target_buffer_id=st.from_regex("^[a-zA-Z0-9_.:-]+$", fullmatch=True).filter(lambda x: 1 <= len(x) <= 128),
    max_schema_depth=st.integers(min_value=1, max_value=10),
    max_properties=st.integers(min_value=1, max_value=1000),
    require_strict_validation=st.booleans(),
)
def test_latent_schema_inference_intent_valid(
    target_buffer_id: str, max_schema_depth: int, max_properties: int, require_strict_validation: bool
) -> None:
    intent = LatentSchemaInferenceIntent(
        target_buffer_id=target_buffer_id,
        max_schema_depth=max_schema_depth,
        max_properties=max_properties,
        require_strict_validation=require_strict_validation,
    )
    assert intent.target_buffer_id == target_buffer_id


@given(minimum_collateral=st.integers(min_value=0, max_value=1000000000), slashing_penalty=st.integers(min_value=0))
def test_market_contract_bounds(minimum_collateral: int, slashing_penalty: int) -> None:
    if slashing_penalty > minimum_collateral:
        with pytest.raises(ValidationError):
            MarketContract(minimum_collateral=minimum_collateral, slashing_penalty=slashing_penalty)
    else:
        contract = MarketContract(minimum_collateral=minimum_collateral, slashing_penalty=slashing_penalty)
        assert contract.minimum_collateral == minimum_collateral


@given(
    trace_id=st.from_regex("^[a-zA-Z0-9_.:-]+$", fullmatch=True).filter(lambda x: 1 <= len(x) <= 128),
    explored_branch_ids=st.lists(
        st.from_regex("^[a-zA-Z0-9_.:-]+$", fullmatch=True).filter(lambda x: 1 <= len(x) <= 128),
        min_size=1,
        unique=True,
    ),
    total_latent_tokens=st.integers(min_value=0, max_value=1000000000),
)
def test_latent_scratchpad_receipt_referential_integrity(
    trace_id: str, explored_branch_ids: list[str], total_latent_tokens: int
) -> None:
    explored_branches = [
        ThoughtBranchState(branch_id=b_id, latent_content_hash="a" * 64, prm_score=0.5) for b_id in explored_branch_ids
    ]

    resolution_id = explored_branch_ids[0]
    discarded_id = explored_branch_ids[-1] if len(explored_branch_ids) > 1 else resolution_id

    receipt = LatentScratchpadReceipt(
        trace_id=trace_id,
        explored_branches=explored_branches,
        resolution_branch_id=resolution_id,
        discarded_branches=[discarded_id],
        total_latent_tokens=total_latent_tokens,
    )
    assert receipt.resolution_branch_id == resolution_id


@given(
    action_space_id=st.from_regex("^[a-zA-Z0-9_.:-]+$", fullmatch=True).filter(lambda x: 1 <= len(x) <= 128),
    tool_names=st.lists(
        st.from_regex("^[a-zA-Z0-9_.:-]+$", fullmatch=True).filter(lambda x: 1 <= len(x) <= 128),
        unique=True,
        min_size=1,
        max_size=5,
    ),
)
def test_action_space_manifest_uniqueness(action_space_id: str, tool_names: list[str]) -> None:
    native_tools = [
        ToolManifest(
            tool_name=name,
            input_schema={"type": "object", "properties": {}},
            description="desc",
            side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
            permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
        )
        for name in tool_names
    ]
    manifest = ActionSpaceManifest(action_space_id=action_space_id, native_tools=native_tools)
    assert [t.tool_name for t in manifest.native_tools] == sorted(tool_names)


@given(
    retracted_nodes=st.lists(st.from_regex("^[a-zA-Z0-9_.:-]+$", fullmatch=True).filter(lambda x: 1 <= len(x) <= 128))
)
def test_epistemic_ledger_state_bounds(retracted_nodes: list[str]) -> None:
    ledger = EpistemicLedgerState(
        history=[],
        defeasible_claims={},
        retracted_nodes=retracted_nodes,
        checkpoints=[],
        active_cascades=[],
        active_rollbacks=[],
        migration_contracts=[],
    )
    assert ledger.retracted_nodes == sorted(retracted_nodes)


@given(
    mutation_paradigm=st.sampled_from(["append_only", "merge_on_resolve"]),
    max_uncommitted_edges=st.integers(min_value=1, max_value=1000000000),
    micro_batch_interval_ms=st.integers(min_value=1, max_value=86400000),
)
def test_continuous_mutation_policy_vram_bounds(
    mutation_paradigm: typing.Any, max_uncommitted_edges: int, micro_batch_interval_ms: int
) -> None:
    if mutation_paradigm == "append_only" and max_uncommitted_edges > 10000:
        with pytest.raises(ValidationError):
            ContinuousMutationPolicy(
                mutation_paradigm=mutation_paradigm,
                max_uncommitted_edges=max_uncommitted_edges,
                micro_batch_interval_ms=micro_batch_interval_ms,
            )
    else:
        policy = ContinuousMutationPolicy(
            mutation_paradigm=mutation_paradigm,
            max_uncommitted_edges=max_uncommitted_edges,
            micro_batch_interval_ms=micro_batch_interval_ms,
        )
        assert policy.mutation_paradigm == mutation_paradigm
