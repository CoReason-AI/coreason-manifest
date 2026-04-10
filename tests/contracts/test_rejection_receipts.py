
import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from coreason_manifest.spec.ontology import EpistemicRejectionReceipt


@given(
    st.one_of(
        st.floats(max_value=-0.0001, allow_nan=False, allow_infinity=False),
        st.just(float("nan")),
        st.just(float("-inf")),
    )
)
def test_kl_divergence_paradox_trapping(invalid_kl_divergence: float) -> None:
    with pytest.raises(ValidationError) as exc_info:
        EpistemicRejectionReceipt(
            failed_projection_cid="valid_projection_cid",
            violated_algebraic_constraint="Constraint X violated.",
            kl_divergence_to_validity=invalid_kl_divergence,
            stochastic_mutation_gradient="Mutation vector XYZ",
        )
    assert "Mathematical paradox" in str(exc_info.value) or "Input should be a valid number" in str(exc_info.value)


@given(
    st.floats(min_value=0.0, max_value=1e10, allow_nan=False, allow_infinity=False),
    st.text(min_size=1, max_size=10000),
)
def test_valid_gradient_space(valid_kl_divergence: float, valid_gradient: str) -> None:
    receipt = EpistemicRejectionReceipt(
        failed_projection_cid="valid_projection_cid",
        violated_algebraic_constraint="Constraint X violated.",
        kl_divergence_to_validity=valid_kl_divergence,
        stochastic_mutation_gradient=valid_gradient,
    )
    assert receipt.kl_divergence_to_validity == valid_kl_divergence
    assert receipt.stochastic_mutation_gradient == valid_gradient
