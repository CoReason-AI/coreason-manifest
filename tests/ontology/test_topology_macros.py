# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Hypothesis property tests for topology macro compile_to_base_topology methods."""

import base64

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    AdversarialMarketTopologyManifest,
    CapabilityForgeTopologyManifest,
    CognitiveAgentNodeProfile,
    CognitiveSwarmDeploymentManifest,
    CognitiveSystemNodeProfile,
    ConsensusFederationTopologyManifest,
    CouncilTopologyManifest,
    DAGTopologyManifest,
    IntentElicitationTopologyManifest,
    NeurosymbolicIngestionTopologyManifest,
    NeurosymbolicVerificationTopologyManifest,
    PredictionMarketPolicy,
    QuorumPolicy,
    SemanticDiscoveryIntent,
    VectorEmbeddingState,
)


def _make_discovery_intent() -> SemanticDiscoveryIntent:
    vec = VectorEmbeddingState(
        vector_base64=base64.b64encode(b"\x00" * 64).decode(),
        dimensionality=16,
        foundation_matrix_name="test-model",
    )
    return SemanticDiscoveryIntent(
        query_vector=vec,
        min_isometry_score=0.5,
        required_structural_types=["type:a"],
    )


# ---------------------------------------------------------------------------
# CognitiveSwarmDeploymentManifest
# ---------------------------------------------------------------------------


class TestCognitiveSwarmDeploymentManifest:
    """Exercise compile_to_base_topology for swarm deployments."""

    @given(
        mechanism=st.sampled_from(["majority", "prediction_market", "pbft"]),
        count=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=10, deadline=None)
    def test_compile_produces_council(self, mechanism: str, count: int) -> None:
        macro = CognitiveSwarmDeploymentManifest(
            swarm_objective_prompt="Test objective",
            agent_node_count=count,
            consensus_mechanism=mechanism,  # type: ignore[arg-type]
        )
        result = macro.compile_to_base_topology()
        assert isinstance(result, CouncilTopologyManifest)
        # count agent nodes + 1 adjudicator
        assert len(result.nodes) == count + 1

    def test_pbft_consensus_structure(self) -> None:
        macro = CognitiveSwarmDeploymentManifest(
            swarm_objective_prompt="PBFT test",
            agent_node_count=3,
            consensus_mechanism="pbft",
        )
        result = macro.compile_to_base_topology()
        assert result.consensus_policy.strategy == "pbft"  # type: ignore[union-attr]
        assert result.consensus_policy.quorum_rules is not None  # type: ignore[union-attr]

    def test_prediction_market_consensus_structure(self) -> None:
        macro = CognitiveSwarmDeploymentManifest(
            swarm_objective_prompt="PM test",
            agent_node_count=2,
            consensus_mechanism="prediction_market",
        )
        result = macro.compile_to_base_topology()
        assert result.consensus_policy.strategy == "prediction_market"  # type: ignore[union-attr]
        assert result.consensus_policy.prediction_market_rules is not None  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# AdversarialMarketTopologyManifest
# ---------------------------------------------------------------------------


class TestAdversarialMarketTopologyManifest:
    """Exercise disjoint set verification and compile_to_base_topology."""

    def _pm(self) -> PredictionMarketPolicy:
        return PredictionMarketPolicy(
            staking_function="quadratic",
            min_liquidity_magnitude=100,
            convergence_delta_threshold=0.1,
        )

    def test_valid_adversarial(self) -> None:
        obj = AdversarialMarketTopologyManifest(
            blue_team_cids=["did:z:blue1"],
            red_team_cids=["did:z:red1"],
            adjudicator_cid="did:z:adj",
            market_rules=self._pm(),
        )
        result = obj.compile_to_base_topology()
        assert isinstance(result, CouncilTopologyManifest)

    def test_overlapping_teams_rejected(self) -> None:
        with pytest.raises(ValidationError, match="both the Blue and Red teams"):
            AdversarialMarketTopologyManifest(
                blue_team_cids=["did:z:x"],
                red_team_cids=["did:z:x"],
                adjudicator_cid="did:z:adj",
                market_rules=self._pm(),
            )

    def test_adjudicator_in_team_rejected(self) -> None:
        with pytest.raises(ValidationError, match="adjudicator cannot be a member"):
            AdversarialMarketTopologyManifest(
                blue_team_cids=["did:z:adj"],
                red_team_cids=["did:z:red1"],
                adjudicator_cid="did:z:adj",
                market_rules=self._pm(),
            )

    def test_teams_sorted(self) -> None:
        obj = AdversarialMarketTopologyManifest(
            blue_team_cids=["did:z:b", "did:z:a"],
            red_team_cids=["did:z:d", "did:z:c"],
            adjudicator_cid="did:z:adj",
            market_rules=self._pm(),
        )
        assert obj.blue_team_cids == sorted(obj.blue_team_cids)
        assert obj.red_team_cids == sorted(obj.red_team_cids)


# ---------------------------------------------------------------------------
# ConsensusFederationTopologyManifest
# ---------------------------------------------------------------------------


class TestConsensusFederationTopologyManifest:
    """Exercise adjudicator isolation and BFT compilation."""

    def _qr(self) -> QuorumPolicy:
        return QuorumPolicy(
            max_tolerable_faults=0,
            min_quorum_size=3,
            state_validation_metric="ledger_hash",
            byzantine_action="quarantine",
        )

    def test_valid_federation(self) -> None:
        obj = ConsensusFederationTopologyManifest(
            participant_cids=["did:z:p1", "did:z:p2", "did:z:p3"],
            adjudicator_cid="did:z:adj",
            quorum_rules=self._qr(),
        )
        result = obj.compile_to_base_topology()
        assert isinstance(result, CouncilTopologyManifest)
        assert result.nodes["did:z:adj"]

    def test_adjudicator_in_participants_rejected(self) -> None:
        with pytest.raises(ValidationError, match="cannot act as a voting participant"):
            ConsensusFederationTopologyManifest(
                participant_cids=["did:z:adj", "did:z:p2", "did:z:p3"],
                adjudicator_cid="did:z:adj",
                quorum_rules=self._qr(),
            )

    def test_participants_sorted(self) -> None:
        obj = ConsensusFederationTopologyManifest(
            participant_cids=["did:z:c", "did:z:a", "did:z:b"],
            adjudicator_cid="did:z:adj",
            quorum_rules=self._qr(),
        )
        assert obj.participant_cids == sorted(obj.participant_cids)


# ---------------------------------------------------------------------------
# NeurosymbolicVerificationTopologyManifest
# ---------------------------------------------------------------------------


class TestNeurosymbolicVerificationTopologyManifest:
    """Exercise bipartite role validation."""

    def test_valid_proposer_verifier(self) -> None:
        obj = NeurosymbolicVerificationTopologyManifest(
            nodes={
                "did:z:proposer": CognitiveAgentNodeProfile(description="Proposer"),
                "did:z:verifier": CognitiveSystemNodeProfile(description="Verifier"),
            },
            proposer_node_cid="did:z:proposer",
            verifier_node_cid="did:z:verifier",
            max_revision_loops=5,
        )
        result = obj.compile_to_base_topology()
        assert isinstance(result, DAGTopologyManifest)

    def test_same_proposer_verifier_rejected(self) -> None:
        with pytest.raises(ValidationError, match="cannot be the same node"):
            NeurosymbolicVerificationTopologyManifest(
                nodes={
                    "did:z:same": CognitiveAgentNodeProfile(description="Both"),
                },
                proposer_node_cid="did:z:same",
                verifier_node_cid="did:z:same",
                max_revision_loops=5,
            )

    def test_proposer_not_agent_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Connectionist Agent"):
            NeurosymbolicVerificationTopologyManifest(
                nodes={
                    "did:z:proposer": CognitiveSystemNodeProfile(description="System acting as proposer"),
                    "did:z:verifier": CognitiveSystemNodeProfile(description="Verifier"),
                },
                proposer_node_cid="did:z:proposer",
                verifier_node_cid="did:z:verifier",
                max_revision_loops=5,
            )

    def test_verifier_not_system_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Deterministic System"):
            NeurosymbolicVerificationTopologyManifest(
                nodes={
                    "did:z:proposer": CognitiveAgentNodeProfile(description="Proposer"),
                    "did:z:verifier": CognitiveAgentNodeProfile(description="Agent acting as verifier"),
                },
                proposer_node_cid="did:z:proposer",
                verifier_node_cid="did:z:verifier",
                max_revision_loops=5,
            )


# ---------------------------------------------------------------------------
# NeurosymbolicIngestionTopologyManifest
# ---------------------------------------------------------------------------


class TestNeurosymbolicIngestionTopologyManifest:
    """Exercise 4-stage pipeline compilation."""

    def test_compile_to_dag(self) -> None:
        obj = NeurosymbolicIngestionTopologyManifest(
            source_artifact_cid="did:z:artifact1",
            compiler_node_cid="did:z:compiler",
            grounding_specialist_cid="did:z:grounding",
            verification_oracle_cid="did:z:verifier",
            archivist_node_cid="did:z:archivist",
        )
        result = obj.compile_to_base_topology()
        assert isinstance(result, DAGTopologyManifest)
        assert len(result.edges) == 3
        assert result.max_depth == 4
        assert result.max_fan_out == 1


# ---------------------------------------------------------------------------
# CapabilityForgeTopologyManifest
# ---------------------------------------------------------------------------


class TestCapabilityForgeTopologyManifest:
    """Exercise forge macro compilation with optional human supervisor."""

    def test_compile_without_human(self) -> None:
        intent = _make_discovery_intent()
        obj = CapabilityForgeTopologyManifest(
            target_epistemic_deficit=intent,
            generator_node_cid="did:z:gen",
            formal_verifier_cid="did:z:verify",
            fuzzing_engine_cid="did:z:fuzz",
            nodes={
                "did:z:gen": CognitiveAgentNodeProfile(description="gen"),
                "did:z:verify": CognitiveSystemNodeProfile(description="verify"),
                "did:z:fuzz": CognitiveSystemNodeProfile(description="fuzz"),
            },
        )
        result = obj.compile_to_base_topology()
        assert isinstance(result, DAGTopologyManifest)
        assert len(result.edges) == 2

    def test_compile_with_human(self) -> None:
        intent = _make_discovery_intent()
        obj = CapabilityForgeTopologyManifest(
            target_epistemic_deficit=intent,
            generator_node_cid="did:z:gen",
            formal_verifier_cid="did:z:verify",
            fuzzing_engine_cid="did:z:fuzz",
            human_supervisor_cid="did:z:human",
            nodes={
                "did:z:gen": CognitiveAgentNodeProfile(description="gen"),
                "did:z:verify": CognitiveSystemNodeProfile(description="verify"),
                "did:z:fuzz": CognitiveSystemNodeProfile(description="fuzz"),
            },
        )
        result = obj.compile_to_base_topology()
        assert isinstance(result, DAGTopologyManifest)
        assert len(result.edges) == 3
        assert "did:z:human" in result.nodes


# ---------------------------------------------------------------------------
# IntentElicitationTopologyManifest
# ---------------------------------------------------------------------------


class TestIntentElicitationTopologyManifest:
    """Exercise cyclic DAG compilation for intent elicitation."""

    def test_compile_to_cyclic_dag(self) -> None:
        obj = IntentElicitationTopologyManifest(
            raw_human_artifact_cid="artifact.1",
            transmuter_node_cid="did:z:transmute",
            scanner_node_cid="did:z:scan",
            human_oracle_cid="did:z:human",
            nodes={
                "did:z:transmute": CognitiveSystemNodeProfile(description="transmuter"),
                "did:z:scan": CognitiveAgentNodeProfile(description="scanner"),
                "did:z:human": CognitiveSystemNodeProfile(description="human"),
            },
        )
        result = obj.compile_to_base_topology()
        assert isinstance(result, DAGTopologyManifest)
        assert result.allow_cycles is True
        assert len(result.edges) == 3
