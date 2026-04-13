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
    obj = ConsensusFederationTopologyManifest.model_construct(  # type: ignore[call-arg]
        topology_class="macro_federation",
        adjudicator_cid="did:example:xxxxxx",
        participant_cids=["did:example:1xxxxx", "did:example:xxxxxx", "did:example:3xxxxx"],
    )
    with pytest.raises(ValueError, match="Adjudicator cannot act as a voting participant"):
        obj.verify_adjudicator_isolation()  # type: ignore[operator]


def test_topological_contradiction_adversarial_participant() -> None:
    obj = AdversarialMarketTopologyManifest.model_construct(  # type: ignore[call-arg]
        topology_class="macro_adversarial",
        adjudicator_cid="did:example:xxxxxx",
        blue_team_cids=["did:example:1xxxxx", "did:example:xxxxxx"],
        red_team_cids=["did:example:2xxxxx", "did:example:3xxxxx"],
    )
    with pytest.raises(ValueError, match="The adjudicator cannot be a member of a competing team"):
        obj.verify_disjoint_sets()  # type: ignore[operator]


def test_topological_fracture_generative_taxonomy() -> None:
    obj = GenerativeTaxonomyManifest.model_construct(  # type: ignore[call-arg]
        root_node_cid="did:example:xxxx",
        nodes={"node_1xxx": {"node_cid": "node_1xxx", "semantic_label": "test"}},  # type: ignore[dict-item]
    )
    with pytest.raises(ValueError, match=r"Topological Fracture: Root node(.*)not found in matrix"):
        obj.verify_dag_integrity()  # type: ignore[operator]


def test_dual_verification_duplication() -> None:
    obj = CognitiveDualVerificationReceipt.model_construct(
        primary_verifier_cid="did:example:1xxx",
        secondary_verifier_cid="did:example:1xxx",
        trace_factual_alignment=True,
    )
    with pytest.raises(ValueError, match="Dual verification requires two distinct"):
        obj.enforce_dual_key_lock()  # type: ignore[operator]


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
