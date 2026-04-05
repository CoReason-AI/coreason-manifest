import pytest

from coreason_manifest.spec.ontology import (
    AlgebraicEffectProfile,
    ComputationalMonadProfile,
    CRDTAlgebraicType,
    PersistenceCommitReceipt,
    ToposSheafValuationContract,
)


def test_algebraic_effect_profile_variance_bound_error() -> None:
    with pytest.raises(ValueError, match=r"thermodynamic_variance_bound must be exactly 0.0"):
        AlgebraicEffectProfile(
            permitted_monads=[ComputationalMonadProfile.READER],
            is_referentially_transparent=True,
            thermodynamic_variance_bound=0.5,
        )


def test_persistence_commit_receipt_merkle_clock_vector() -> None:
    receipt = PersistenceCommitReceipt(
        event_id="evt-1",
        timestamp=1234567890.0,
        lakehouse_snapshot_id="snap-1",
        committed_state_diff_id="diff-1",
        target_table_uri="s3://bucket/table",
        crdt_algebraic_type=CRDTAlgebraicType.LWW_REGISTER,
        merkle_clock_vector={"did:node:a-id": 1, "did:node:b-id": 2},
    )
    assert receipt.merkle_clock_vector == {"did:node:a-id": 1, "did:node:b-id": 2}


def test_topos_sheaf_valuation_contract_sorts_subgraph_nodes() -> None:
    contract = ToposSheafValuationContract(
        valuation_id="val-1",
        subgraph_nodes=[
            "did:node:b-id",
            "did:node:a-id",
        ],
        local_truth_value=1.0,
        consistency_proof_hash="a" * 64,
    )
    assert contract.subgraph_nodes == ["did:node:a-id", "did:node:b-id"]
