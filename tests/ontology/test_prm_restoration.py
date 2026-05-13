# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    CognitiveStateProfile,
    DynamicConvergenceSLA,
    EpistemicSOPManifest,
    ProcessRewardContract,
)


def test_prm_restoration_instantiation() -> None:
    """Tests the instantiation of restored PRM schemas."""
    sla = DynamicConvergenceSLA(convergence_delta_epsilon=0.95, lookback_window_steps=10, minimum_reasoning_steps=5)

    reward = ProcessRewardContract(
        pruning_threshold=0.8, max_backtracks_allowed=10, evaluator_matrix_name="eval_1", convergence_sla=sla
    )

    step_profile = CognitiveStateProfile(urgency_index=0.5, caution_index=0.5, divergence_tolerance=0.5)

    sop = EpistemicSOPManifest(
        sop_cid="sop_123",
        target_persona="persona_abc",
        cognitive_steps={"step_1": step_profile},
        structural_grammar_hashes={"step_1": "hash_1"},
        chronological_flow_edges=[],
        prm_evaluations=[reward],
    )

    assert sop.sop_cid == "sop_123"
    assert len(sop.prm_evaluations) == 1
    assert sop.prm_evaluations[0].pruning_threshold == 0.8
    assert sop.prm_evaluations[0].convergence_sla is not None
    assert sop.prm_evaluations[0].convergence_sla.convergence_delta_epsilon == 0.95


def test_prm_restoration_json_isomorphism() -> None:
    """Tests JSON isomorphism for restored PRM schemas."""
    reward = ProcessRewardContract(pruning_threshold=0.9, max_backtracks_allowed=5, evaluator_matrix_name="eval_2")

    step_profile = CognitiveStateProfile(urgency_index=0.1, caution_index=0.9, divergence_tolerance=0.1)

    sop = EpistemicSOPManifest(
        sop_cid="sop_456",
        target_persona="persona_xyz",
        cognitive_steps={"step_2": step_profile},
        structural_grammar_hashes={"step_2": "hash_2"},
        chronological_flow_edges=[],
        prm_evaluations=[reward],
    )

    json_data = sop.model_dump_json()
    rehydrated = EpistemicSOPManifest.model_validate_json(json_data)

    assert rehydrated.sop_cid == sop.sop_cid
    assert rehydrated.prm_evaluations[0].pruning_threshold == 0.9


def test_sop_manifest_ghost_node_validation() -> None:
    """Tests that EpistemicSOPManifest rejects ghost nodes in flow edges and grammar hashes."""
    step_profile = CognitiveStateProfile(urgency_index=0.5, caution_index=0.5, divergence_tolerance=0.5)

    # Test ghost node in chronological_flow_edges
    with pytest.raises(ValidationError, match="Ghost node referenced in chronological_flow_edges source: step_unknown"):
        EpistemicSOPManifest(
            sop_cid="sop_ghost_1",
            target_persona="persona_ghost",
            cognitive_steps={"step_1": step_profile},
            structural_grammar_hashes={"step_1": "hash_1"},
            chronological_flow_edges=[("step_unknown", "step_1")],
            prm_evaluations=[],
        )

    with pytest.raises(ValidationError, match="Ghost node referenced in chronological_flow_edges target: step_unknown"):
        EpistemicSOPManifest(
            sop_cid="sop_ghost_2",
            target_persona="persona_ghost",
            cognitive_steps={"step_1": step_profile},
            structural_grammar_hashes={"step_1": "hash_1"},
            chronological_flow_edges=[("step_1", "step_unknown")],
            prm_evaluations=[],
        )

    # Test ghost node in structural_grammar_hashes
    with pytest.raises(ValidationError, match="Ghost node referenced in structural_grammar_hashes: step_unknown"):
        EpistemicSOPManifest(
            sop_cid="sop_ghost_3",
            target_persona="persona_ghost",
            cognitive_steps={"step_1": step_profile},
            structural_grammar_hashes={"step_unknown": "hash_1"},
            chronological_flow_edges=[],
            prm_evaluations=[],
        )
