from datetime import UTC, datetime

import pytest

from coreason_manifest.compute.argumentation import ArgumentationDAG, DefeasibleClaim
from coreason_manifest.compute.uncertainty import SyntaxTreeCitationAnchor


def test_defeasible_claim() -> None:
    anchor = SyntaxTreeCitationAnchor(
        pmcid="PMC12345",
        source_text_tokens=["patient", "has", "hypertension"],
        retrieval_timestamp=datetime.now(UTC),
        guideline_version="1.0",
    )
    claim = DefeasibleClaim(
        claim_id="claim_1",
        agent_id="agent_a",
        claim_type="PROPOSAL",
        semantic_reasoning="The patient exhibits symptoms.",
        citation_anchors=[anchor],
    )
    assert claim.claim_id == "claim_1"
    assert claim.claim_type == "PROPOSAL"
    assert len(claim.citation_anchors) == 1


def test_argumentation_dag() -> None:
    anchor = SyntaxTreeCitationAnchor(
        pmcid="PMC12345",
        source_text_tokens=["patient", "has", "hypertension"],
        retrieval_timestamp=datetime.now(UTC),
        guideline_version="1.0",
    )
    claim1 = DefeasibleClaim(
        claim_id="claim_1",
        agent_id="agent_a",
        claim_type="PROPOSAL",
        semantic_reasoning="The patient exhibits symptoms.",
        citation_anchors=[anchor],
    )
    claim2 = DefeasibleClaim(
        claim_id="claim_2",
        agent_id="agent_b",
        claim_type="REBUTTAL",
        target_claim_id="claim_1",
        semantic_reasoning="Symptoms are non-specific.",
        citation_anchors=[],
    )

    dag = ArgumentationDAG(
        graph_id="dag_1",
        target_phenotype_id="phenotype_X",
        claims={"claim_1": claim1, "claim_2": claim2},
        resolution_status="UNRESOLVED",
    )
    assert dag.graph_id == "dag_1"
    assert dag.resolution_status == "UNRESOLVED"
    assert len(dag.claims) == 2
    assert dag.claims["claim_2"].target_claim_id == "claim_1"

    with pytest.raises(ValueError, match="1 validation error for"):
        ArgumentationDAG(
            graph_id="dag_1",
            target_phenotype_id="phenotype_X",
            claims={"claim_1": claim1},
            resolution_status="INVALID_STATUS",  # type: ignore
        )


def test_defeasible_claim_validation() -> None:
    anchor = SyntaxTreeCitationAnchor(
        pmcid="PMC12345",
        source_text_tokens=["patient", "has", "hypertension"],
        retrieval_timestamp=datetime.now(UTC),
        guideline_version="1.0",
    )
    with pytest.raises(ValueError, match="MUST have a target_claim_id"):
        DefeasibleClaim(
            claim_id="claim_1",
            agent_id="agent_a",
            claim_type="REBUTTAL",
            target_claim_id=None,
            semantic_reasoning="Symptoms are non-specific.",
            citation_anchors=[anchor],
        )

    with pytest.raises(ValueError, match="MUST have a target_claim_id"):
        DefeasibleClaim(
            claim_id="claim_2",
            agent_id="agent_a",
            claim_type="UNDERCUT",
            semantic_reasoning="Methodology was flawed.",
            citation_anchors=[anchor],
        )

def test_defeasible_claim_proposal_validation() -> None:
    anchor = SyntaxTreeCitationAnchor(
        pmcid="PMC12345",
        source_text_tokens=["patient", "has", "hypertension"],
        retrieval_timestamp=datetime.now(UTC),
        guideline_version="1.0"
    )
    with pytest.raises(ValueError, match="1 validation error for"):
        DefeasibleClaim(
            claim_id="claim_1",
            agent_id="agent_a",
            claim_type="PROPOSAL",
            target_claim_id="some_other_claim",
            semantic_reasoning="The patient exhibits symptoms.",
            citation_anchors=[anchor]
        )

def test_argumentation_dag_validation() -> None:
    anchor = SyntaxTreeCitationAnchor(
        pmcid="PMC12345",
        source_text_tokens=["patient", "has", "hypertension"],
        retrieval_timestamp=datetime.now(UTC),
        guideline_version="1.0"
    )
    claim1 = DefeasibleClaim(
        claim_id="claim_1",
        agent_id="agent_a",
        claim_type="PROPOSAL",
        semantic_reasoning="The patient exhibits symptoms.",
        citation_anchors=[anchor]
    )
    claim2 = DefeasibleClaim(
        claim_id="claim_2",
        agent_id="agent_b",
        claim_type="REBUTTAL",
        target_claim_id="non_existent_claim",
        semantic_reasoning="Symptoms are non-specific.",
        citation_anchors=[]
    )

    with pytest.raises(ValueError, match="1 validation error for"):
        ArgumentationDAG(
            graph_id="dag_1",
            target_phenotype_id="phenotype_X",
            claims={"claim_1": claim1, "claim_2": claim2},
            resolution_status="UNRESOLVED"
        )
