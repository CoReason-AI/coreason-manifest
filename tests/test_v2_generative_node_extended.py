# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import (
    GenerativeNode,
    GraphTopology,
    RecipeDefinition,
    RecipeInterface,
    SolverConfig,
    SolverStrategy,
)


def test_solver_config_serialization() -> None:
    """Test serialization of SolverConfig."""
    config = SolverConfig(strategy=SolverStrategy.ENSEMBLE, n_samples=5, aggregation_method="best_of_n")
    data = config.model_dump()
    assert data["strategy"] == "ensemble"
    assert data["n_samples"] == 5


def test_solver_config_validation_edge_cases() -> None:
    """Test numeric boundaries for SolverConfig fields."""
    with pytest.raises(ValidationError) as exc:
        SolverConfig(depth_limit=0)
    assert "Input should be greater than or equal to 1" in str(exc.value)


def test_solver_config_invalid_strategy() -> None:
    """Test invalid strategy enum value (Pydantic validation)."""
    # Use Any cast to bypass MyPy check for invalid literal
    invalid_strategy: Any = "invalid_strategy"
    with pytest.raises(ValidationError) as exc:
        SolverConfig(strategy=invalid_strategy)
    assert "Input should be 'standard', 'tree_search' or 'ensemble'" in str(exc.value)


def test_generative_node_with_custom_solver() -> None:
    """Test GenerativeNode correctly embeds a custom SolverConfig."""
    solver = SolverConfig(strategy=SolverStrategy.TREE_SEARCH, max_iterations=100, beam_width=5)
    node = GenerativeNode(id="gen-node", goal="Solve complex logic", output_schema={}, solver=solver)

    assert node.solver.strategy == SolverStrategy.TREE_SEARCH
    assert node.solver.max_iterations == 100
    dump = node.model_dump()
    assert dump["solver"]["max_iterations"] == 100


def test_full_recipe_serialization_with_complex_solver() -> None:
    """Test full round-trip serialization of a Recipe containing advanced GenerativeNodes."""
    node_ensemble = GenerativeNode(
        id="step-1",
        goal="Generate ideas",
        output_schema={"type": "array"},
        solver=SolverConfig(strategy=SolverStrategy.ENSEMBLE, n_samples=10, aggregation_method="weighted_merge"),
    )

    node_refine = GenerativeNode(
        id="step-2",
        goal="Refine best idea",
        output_schema={"type": "string"},
        solver=SolverConfig(strategy=SolverStrategy.TREE_SEARCH, depth_limit=10, beam_width=2),
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Complex Solver Recipe"),
        interface=RecipeInterface(),
        topology=GraphTopology(
            nodes=[node_ensemble, node_refine], edges=[{"source": "step-1", "target": "step-2"}], entry_point="step-1"
        ),
    )

    # Serialize
    json_str = recipe.model_dump_json()
    loaded = RecipeDefinition.model_validate_json(json_str)

    nodes = {n.id: n for n in loaded.topology.nodes}

    step1 = nodes["step-1"]
    assert isinstance(step1, GenerativeNode)
    assert step1.solver.strategy == SolverStrategy.ENSEMBLE
    assert step1.solver.n_samples == 10

    step2 = nodes["step-2"]
    assert isinstance(step2, GenerativeNode)
    assert step2.solver.strategy == SolverStrategy.TREE_SEARCH
    assert step2.solver.depth_limit == 10


def test_complex_overlapping_solver_config() -> None:
    """
    Test a configuration that sets parameters relevant to multiple strategies.
    """
    # Setting both n_samples (SPIO) and beam_width (LATS)
    solver = SolverConfig(
        strategy=SolverStrategy.STANDARD,  # Strategy is standard
        n_samples=5,  # But we set SPIO param
        beam_width=3,  # And LATS param
        max_iterations=50,
    )

    # Should validate fine as a data structure
    node = GenerativeNode(id="mixed-config", goal="Ambiguous task", output_schema={}, solver=solver)

    assert node.solver.n_samples == 5
    assert node.solver.beam_width == 3
