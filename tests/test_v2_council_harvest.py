import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.recipe import GenerativeNode, SolverConfig, SolverStrategy


def test_solver_config_default_behavior() -> None:
    """
    Test Case 1: Default Behavior
    - Instantiate GenerativeNode with default SolverConfig.
    - Verify enable_dissenter is False.
    - Verify diversity_threshold is 0.3.
    """
    # Create a minimal valid GenerativeNode
    node = GenerativeNode(
        id="gen_node_1",
        goal="Solve world peace",
        output_schema={"type": "object"},
        solver=SolverConfig(),
    )

    assert node.solver.enable_dissenter is False
    assert node.solver.diversity_threshold == 0.3
    assert node.solver.consensus_threshold == 0.6
    assert node.solver.n_samples == 1


def test_solver_config_advanced_council() -> None:
    """
    Test Case 2: Advanced Council Configuration
    - Instantiate GenerativeNode with custom settings.
    - Verify serialization.
    - Verify ValidationError for out of bounds consensus_threshold.
    """
    solver_config = SolverConfig(
        strategy=SolverStrategy.ENSEMBLE,
        n_samples=5,
        enable_dissenter=True,
        consensus_threshold=0.8,
        diversity_threshold=0.5,
    )

    node = GenerativeNode(
        id="gen_node_council",
        goal="Complex decision making",
        output_schema={"type": "object"},
        solver=solver_config,
    )

    # Verify fields
    assert node.solver.strategy == SolverStrategy.ENSEMBLE
    assert node.solver.n_samples == 5
    assert node.solver.enable_dissenter is True
    assert node.solver.consensus_threshold == 0.8
    assert node.solver.diversity_threshold == 0.5

    # Serialization check
    serialized = node.model_dump(mode="json")
    solver_data = serialized["solver"]
    assert solver_data["strategy"] == "ensemble"
    assert solver_data["n_samples"] == 5
    assert solver_data["enable_dissenter"] is True
    assert solver_data["consensus_threshold"] == 0.8
    assert solver_data["diversity_threshold"] == 0.5

    # Validation Error Check
    with pytest.raises(ValidationError) as excinfo:
        SolverConfig(consensus_threshold=1.5)

    # We can check if the error message mentions the field
    assert "consensus_threshold" in str(excinfo.value)
