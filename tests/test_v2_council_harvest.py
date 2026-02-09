# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

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


def test_solver_config_edge_cases() -> None:
    """
    Test Case 3: Edge Cases
    - Threshold boundaries (0.0, 1.0).
    - Logical oddity: n_samples=1 with dissenter (should be valid schema-wise).
    - Slightly out of bounds values.
    """
    # 1. Boundary Values
    config_boundaries = SolverConfig(
        strategy=SolverStrategy.ENSEMBLE,
        diversity_threshold=0.0,  # Min
        consensus_threshold=1.0,  # Max
        enable_dissenter=False,
    )
    assert config_boundaries.diversity_threshold == 0.0
    assert config_boundaries.consensus_threshold == 1.0

    # 2. Logical Oddity (Valid Schema)
    # A single agent council with a dissenter is weird but valid Pydantic
    config_weird = SolverConfig(
        strategy=SolverStrategy.ENSEMBLE,
        n_samples=1,
        enable_dissenter=True,
    )
    assert config_weird.n_samples == 1
    assert config_weird.enable_dissenter is True

    # 3. Slightly Out of Bounds (Fail)
    with pytest.raises(ValidationError):
        SolverConfig(consensus_threshold=1.000001)

    with pytest.raises(ValidationError):
        SolverConfig(diversity_threshold=-0.000001)


def test_solver_config_complex_cases() -> None:
    """
    Test Case 4: Complex Cases
    - Hybrid Config (Tree Search + Ensemble fields set together).
    - Full Round Trip Serialization.
    """
    # 1. Hybrid Config
    # Setting both LATS (beam_width) and Council (diversity) fields
    # This is valid because SolverConfig is a single model covering all strategies
    hybrid_config = SolverConfig(
        strategy=SolverStrategy.TREE_SEARCH,  # Strategy says Tree
        beam_width=5,  # LATS param
        max_iterations=20,  # LATS param
        diversity_threshold=0.8,  # Council param (should be ignored by logic but valid in schema)
        enable_dissenter=True,  # Council param
    )

    assert hybrid_config.strategy == SolverStrategy.TREE_SEARCH
    assert hybrid_config.beam_width == 5
    assert hybrid_config.diversity_threshold == 0.8

    # 2. Full Round Trip
    node_original = GenerativeNode(
        id="round_trip_node",
        goal="Testing persistence",
        output_schema={"type": "string"},
        solver=hybrid_config,
    )

    # Serialize to dict (JSON-like)
    node_dict = node_original.model_dump(mode="json")

    # Deserialize back to object
    node_restored = GenerativeNode.model_validate(node_dict)

    # Verify equality
    assert node_restored.id == node_original.id
    assert node_restored.solver.strategy == node_original.solver.strategy
    assert node_restored.solver.diversity_threshold == node_original.solver.diversity_threshold
    assert node_restored.solver.beam_width == node_original.solver.beam_width
