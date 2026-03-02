import pytest
from pydantic import ValidationError

from coreason_manifest.core.oversight.governance import (
    DriftMeasurementMethod,
    DriftPolicy,
    Governance,
)
from coreason_manifest.core.oversight.resilience import (
    ContextPruningStrategy,
    ErrorDomain,
    ErrorHandler,
    TutorAlignmentStrategy,
)


def test_drift_policy_instantiation() -> None:
    """Test standard instantiation of DriftPolicy."""
    policy = DriftPolicy(
        input_drift_threshold=0.1,
        output_drift_threshold=0.2,
        trajectory_divergence_limit=0.15,
        baseline_dataset_id="golden_set_v1",
        measurement_method=DriftMeasurementMethod.COSINE_DISTANCE,
    )
    assert policy.input_drift_threshold == 0.1
    assert policy.output_drift_threshold == 0.2
    assert policy.trajectory_divergence_limit == 0.15
    assert policy.baseline_dataset_id == "golden_set_v1"
    assert policy.measurement_method == DriftMeasurementMethod.COSINE_DISTANCE


def test_drift_policy_constraints() -> None:
    """Test bound checks for drift threshold fields."""
    with pytest.raises(ValidationError):
        DriftPolicy(
            input_drift_threshold=-0.1,
            output_drift_threshold=0.2,
            trajectory_divergence_limit=0.15,
            baseline_dataset_id="golden_set_v1",
            measurement_method=DriftMeasurementMethod.JACCARD_INDEX,
        )

    with pytest.raises(ValidationError):
        DriftPolicy(
            input_drift_threshold=0.1,
            output_drift_threshold=1.1,
            trajectory_divergence_limit=0.15,
            baseline_dataset_id="golden_set_v1",
            measurement_method=DriftMeasurementMethod.JACCARD_INDEX,
        )

    with pytest.raises(ValidationError):
        DriftPolicy(
            input_drift_threshold=0.1,
            output_drift_threshold=0.2,
            trajectory_divergence_limit=-0.05,
            baseline_dataset_id="golden_set_v1",
            measurement_method=DriftMeasurementMethod.EPISTEMIC_FALSIFICATION,
        )


def test_governance_with_drift_policy() -> None:
    """Test Governance model accepts the new DriftPolicy."""
    drift_policy = DriftPolicy(
        input_drift_threshold=0.05,
        output_drift_threshold=0.1,
        trajectory_divergence_limit=0.3,
        measurement_method=DriftMeasurementMethod.EPISTEMIC_FALSIFICATION,
    )

    governance = Governance(
        active_middlewares=[],
        drift=drift_policy,
    )

    assert governance.drift is not None
    assert governance.drift.input_drift_threshold == 0.05
    assert governance.drift.measurement_method == DriftMeasurementMethod.EPISTEMIC_FALSIFICATION


def test_context_pruning_strategy_instantiation() -> None:
    """Test standard instantiation of ContextPruningStrategy."""
    strategy = ContextPruningStrategy(
        eviction_target="oldest_messages",
        prune_percentage=0.25,
    )
    assert strategy.type == "context_pruning"
    assert strategy.eviction_target == "oldest_messages"
    assert strategy.prune_percentage == 0.25


def test_context_pruning_strategy_constraints() -> None:
    """Test constraint checks on prune_percentage."""
    with pytest.raises(ValidationError):
        ContextPruningStrategy(
            eviction_target="oldest_messages",
            prune_percentage=0.0,
        )
    with pytest.raises(ValidationError):
        ContextPruningStrategy(
            eviction_target="lowest_salience",
            prune_percentage=1.1,
        )


def test_tutor_alignment_strategy_instantiation() -> None:
    """Test standard instantiation of TutorAlignmentStrategy."""
    strategy = TutorAlignmentStrategy(
        system_prompt_override="Do better.",
        reset_trajectory=True,
    )
    assert strategy.type == "tutor_alignment"
    assert strategy.system_prompt_override == "Do better."
    assert strategy.reset_trajectory is True


def test_mapping_strategies_to_error_domain() -> None:
    """Test mapping strategies to ErrorDomain.DRIFT within an ErrorHandler."""
    context_pruning = ContextPruningStrategy(eviction_target="lowest_salience", prune_percentage=0.5)
    tutor_alignment = TutorAlignmentStrategy(system_prompt_override="Align strictly.", reset_trajectory=False)

    handler1 = ErrorHandler(
        match_domain=[ErrorDomain.DRIFT],
        strategy=context_pruning,
    )

    handler2 = ErrorHandler(
        match_domain=[ErrorDomain.ALIGNMENT],
        strategy=tutor_alignment,
    )

    assert handler1.match_domain == [ErrorDomain.DRIFT]
    assert handler1.strategy.type == "context_pruning"
    assert isinstance(handler1.strategy, ContextPruningStrategy)
    assert handler1.strategy.eviction_target == "lowest_salience"

    assert handler2.match_domain == [ErrorDomain.ALIGNMENT]
    assert handler2.strategy.type == "tutor_alignment"
    assert isinstance(handler2.strategy, TutorAlignmentStrategy)
    assert handler2.strategy.reset_trajectory is False
