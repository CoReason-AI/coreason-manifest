import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import ActiveInferenceEpoch, EpistemicRejectionReceipt

receipt_strategy = st.builds(
    EpistemicRejectionReceipt,
    receipt_cid=st.uuids().map(str),
    failed_projection_cid=st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-"),
    violated_algebraic_constraint=st.text(min_size=1, max_size=2000),
    kl_divergence_to_validity=st.floats(min_value=0.0, max_value=1e10, allow_nan=False, allow_infinity=False),
    stochastic_mutation_gradient=st.text(min_size=1, max_size=100000),
)


@given(st.lists(receipt_strategy), st.floats(min_value=0.0, max_value=1e10, allow_nan=False, allow_infinity=False))
def test_referential_integrity_and_canonical_sorting(
    rejection_history: list[EpistemicRejectionReceipt], valid_free_energy: float
) -> None:
    epoch = ActiveInferenceEpoch(
        epoch_cid="test",
        rejection_history=rejection_history,
        current_free_energy=valid_free_energy,
    )
    assert epoch.current_free_energy >= 0.0

    # Check that it's deterministically sorted by receipt_cid
    cids = [receipt.receipt_cid for receipt in epoch.rejection_history]
    assert cids == sorted(cids)


@given(
    st.lists(receipt_strategy, min_size=1),
    st.floats(min_value=0.0, max_value=1e10, allow_nan=False, allow_infinity=False),
)
def test_serialization_isomorphism(
    rejection_history: list[EpistemicRejectionReceipt], valid_free_energy: float
) -> None:
    epoch = ActiveInferenceEpoch(
        epoch_cid="test",
        rejection_history=rejection_history,
        current_free_energy=valid_free_energy,
    )

    # Serialize to canonical JSON
    serialized = epoch.model_dump_canonical()

    # Deserialize back
    deserialized = ActiveInferenceEpoch.model_validate_json(serialized)

    assert deserialized.epoch_cid == epoch.epoch_cid
    assert deserialized.current_free_energy == epoch.current_free_energy

    cids_original = [receipt.receipt_cid for receipt in epoch.rejection_history]
    cids_deserialized = [receipt.receipt_cid for receipt in deserialized.rejection_history]
    assert cids_original == cids_deserialized


@given(
    st.lists(receipt_strategy),
    st.one_of(
        st.floats(max_value=-0.0001, allow_nan=False, allow_infinity=False),
        st.just(float("nan")),
        st.just(float("-inf")),
    ),
)
def test_free_energy_paradox_trapping(
    rejection_history: list[EpistemicRejectionReceipt], invalid_free_energy: float
) -> None:
    with pytest.raises(ValidationError) as exc_info:
        ActiveInferenceEpoch(
            epoch_cid="test",
            rejection_history=rejection_history,
            current_free_energy=invalid_free_energy,
        )
    assert "Mathematical paradox" in str(exc_info.value) or "Input should be a valid number" in str(exc_info.value)
