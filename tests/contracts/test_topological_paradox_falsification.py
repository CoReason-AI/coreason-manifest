import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import (
    AdversarialMarketTopologyManifest,
    CognitiveDualVerificationReceipt,
    ConsensusFederationTopologyManifest,
    EvaluatorOptimizerTopologyManifest,
    GenerativeTaxonomyManifest,
)


def test_topological_contradiction_council_participant() -> None:
    with pytest.raises(ValidationError, match="Adjudicator cannot act as a voting participant"):
        ConsensusFederationTopologyManifest.model_validate(
            {
                "topology_class": "macro_federation",
                "manifest_cid": "did:example:manifest1",
                "adjudicator_cid": "did:example:xxxxxx",
                "participant_cids": ["did:example:1xxxxx", "did:example:xxxxxx", "did:example:3xxxxx"],
                "quorum_rules": {
                    "max_tolerable_faults": 1,
                    "min_quorum_size": 2,
                    "state_validation_metric": "zk_proof",
                    "byzantine_action": "quarantine",
                },
            }
        )


def test_topological_contradiction_adversarial_participant() -> None:
    with pytest.raises(ValidationError, match="The adjudicator cannot be a member of a competing team"):
        AdversarialMarketTopologyManifest.model_validate(
            {
                "topology_class": "macro_adversarial",
                "manifest_cid": "did:example:manifest1",
                "adjudicator_cid": "did:example:xxxxxx",
                "blue_team_cids": ["did:example:1xxxxx", "did:example:xxxxxx"],
                "red_team_cids": ["did:example:2xxxxx", "did:example:3xxxxx"],
                "market_rules": {
                    "staking_function": "linear",
                    "min_liquidity_magnitude": 1000,
                    "convergence_delta_threshold": 0.01,
                },
            }
        )


def test_topological_fracture_generative_taxonomy() -> None:
    with pytest.raises(ValidationError, match=r"Topological Fracture: Root node(.*)not found in matrix"):
        GenerativeTaxonomyManifest.model_validate(
            {
                "topology_class": "generative",
                "manifest_cid": "did:example:manifest1",
                "root_node_cid": "did:example:xxxx",
                "nodes": {"node_1xxx": {"node_cid": "node_1xxx", "semantic_label": "test"}},
            }
        )


def test_dual_verification_duplication() -> None:
    with pytest.raises(ValidationError, match="Dual verification requires two distinct"):
        CognitiveDualVerificationReceipt.model_validate(
            {
                "receipt_cid": "did:example:manifest1",
                "receipt_class": "dual_verification",
                "primary_verifier_cid": "did:example:1xxx",
                "secondary_verifier_cid": "did:example:1xxx",
                "trace_factual_alignment": True,
                "verified_trace_cid": "t1",
                "resolution_timestamp": 1,
                "justification": "x",
            }
        )


def test_evaluator_optimizer_generator_missing() -> None:
    with pytest.raises(ValidationError, match="not found in topology nodes"):
        EvaluatorOptimizerTopologyManifest.model_validate(
            {
                "topology_class": "evaluator_optimizer",
                "generator_node_cid": "did:example:123",
                "evaluator_node_cid": "did:example:456",
                "max_revision_loops": 5,
                "nodes": {},
            }
        )
