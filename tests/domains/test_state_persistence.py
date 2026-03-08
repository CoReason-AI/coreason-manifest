import pytest
from pydantic import ValidationError

from coreason_manifest.state.persistence import ContinuousMutationPolicy


def test_continuous_mutation_policy_valid() -> None:
    policy = ContinuousMutationPolicy(
        mutation_paradigm="append_only",
        max_uncommitted_rows=5000,
        micro_batch_interval_ms=1000,
    )
    assert policy.max_uncommitted_rows == 5000


def test_continuous_mutation_policy_oom_prevention() -> None:
    with pytest.raises(ValidationError, match="max_uncommitted_rows must be <= 10000"):
        ContinuousMutationPolicy(
            mutation_paradigm="append_only",
            max_uncommitted_rows=15000,
            micro_batch_interval_ms=1000,
        )


def test_continuous_mutation_policy_mor_allows_larger_bounds() -> None:
    policy = ContinuousMutationPolicy(
        mutation_paradigm="merge_on_read",
        max_uncommitted_rows=50000,
        micro_batch_interval_ms=5000,
    )
    assert policy.max_uncommitted_rows == 50000


def test_lakehouse_persistence_contract_instantiation() -> None:
    from coreason_manifest.state.persistence import (
        GraphFlatteningDirective,
        LakehouseMountConfig,
        LakehousePersistenceContract,
    )

    contract = LakehousePersistenceContract(
        contract_id="contract-1234",
        artifact_event_id="artifact-9876",
        mount_config=LakehouseMountConfig(
            catalog_uri="thrift://localhost:9083", table_format="iceberg", schema_evolution_mode="strict"
        ),
        mutation_policy=ContinuousMutationPolicy(
            mutation_paradigm="append_only", max_uncommitted_rows=5000, micro_batch_interval_ms=1000
        ),
        flattening_directive=GraphFlatteningDirective(
            node_projection_mode="wide_columnar",
            edge_projection_mode="adjacency_list",
            preserve_cryptographic_lineage=True,
        ),
    )
    assert contract.contract_id == "contract-1234"
    assert contract.artifact_event_id == "artifact-9876"
    assert contract.mount_config.table_format == "iceberg"
    assert contract.mutation_policy.mutation_paradigm == "append_only"
    assert contract.flattening_directive.node_projection_mode == "wide_columnar"
