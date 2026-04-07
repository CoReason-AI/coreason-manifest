import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import EpistemicMappingContract, NodeCIDState

def test_epistemic_mapping_contract_canonical_sort() -> None:
    contract = EpistemicMappingContract(
        mapping_contract_id="contract-123",
        source_dialect_keys=["key_b", "key_c", "key_a"],
        target_dids=["did:example:z", "did:example:y", "did:example:x"],
        mapping_rules=[
            {"rule2": 2},
            {"rule1": 1},
        ]
    )

    # Ensure source_dialect_keys is sorted
    assert contract.source_dialect_keys == ["key_a", "key_b", "key_c"]

    # Ensure target_dids is sorted
    assert contract.target_dids == ["did:example:x", "did:example:y", "did:example:z"]

    # Ensure mapping_rules is NOT sorted (Topological Exemption)
    assert contract.mapping_rules == [{"rule2": 2}, {"rule1": 1}]
