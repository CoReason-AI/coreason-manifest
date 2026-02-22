from collections import deque
from unittest.mock import patch

import pytest
from jsonschema.exceptions import SchemaError

from coreason_manifest.spec.core.flow import DataSchema, FlowDefinitions, FlowMetadata, LinearFlow
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile, SwarmNode
from coreason_manifest.spec.core.tools import ToolCapability, ToolPack


def test_flow_integrity_coverage() -> None:
    """Cover lines 300-331 in flow.py: validate_integrity logic."""

    # 1. Tool Packs (lines 300-301)
    # Note: ToolPack takes list[ToolCapability]
    tool = ToolCapability(name="my-tool", description="test")
    # ToolPack signature: kind, namespace, tools, dependencies, env_vars
    pack = ToolPack(kind="ToolPack", namespace="pack1", tools=[tool], dependencies=[], env_vars=[])
    definitions = FlowDefinitions(tool_packs={"p1": pack})

    # Agent with valid tool
    agent = AgentNode(
        id="a1",
        type="agent",
        metadata={},
        profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None),
        tools=["my-tool"],
        resilience=None,
    )

    # Should pass
    LinearFlow(
        kind="LinearFlow",
        status="published",
        metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
        definitions=definitions,
        steps=[agent],
    )

    # 2. Invalid Resilience Ref Format (lines 313)
    agent_bad_ref = AgentNode(
        id="a2",
        type="agent",
        metadata={},
        profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None),
        tools=[],
        resilience="invalid_format",
    )

    with pytest.raises(ValueError, match="invalid resilience reference"):
        LinearFlow(
            kind="LinearFlow",
            status="published",
            metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
            definitions=definitions,
            steps=[agent_bad_ref],
        )

    # 3. Invalid Resilience Ref ID (lines 310-311)
    agent_missing_ref = AgentNode(
        id="a3",
        type="agent",
        metadata={},
        profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None),
        tools=[],
        resilience="ref:missing",
    )

    with pytest.raises(ValueError, match="references undefined supervision template"):
        LinearFlow(
            kind="LinearFlow",
            status="published",
            metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
            definitions=definitions,
            steps=[agent_missing_ref],
        )

    # 4. Invalid Profile Ref (lines 319-320)
    agent_missing_profile = AgentNode(
        id="a4", type="agent", metadata={}, profile="missing-profile", tools=[], resilience=None
    )

    with pytest.raises(ValueError, match="references undefined profile ID"):
        LinearFlow(
            kind="LinearFlow",
            status="published",
            metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
            definitions=definitions,
            steps=[agent_missing_profile],
        )

    # 5. SwarmNode Invalid Profile Ref (lines 330-333)
    swarm_missing = SwarmNode(
        id="s1",
        type="swarm",
        metadata={},
        resilience=None,
        worker_profile="missing-worker",
        workload_variable="v",
        distribution_strategy="sharded",
        max_concurrency=1,
        reducer_function="concat",
        output_variable="o",
    )

    with pytest.raises(ValueError, match="references undefined worker profile ID"):
        LinearFlow(
            kind="LinearFlow",
            status="published",
            metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
            definitions=definitions,
            steps=[swarm_missing],
        )


def test_schema_strict_validation_failure() -> None:
    """Cover strict validation exception handling in flow.py: validate_meta_schema."""
    # We want check_schema to fail, causing an immediate exception.

    with patch("jsonschema.Draft7Validator.check_schema") as mock_check:
        mock_check.side_effect = SchemaError("Strict Validation Error")

        # We need a schema that triggers the logic
        bad_schema = {"type": "bad_type"}  # This calls check_schema

        with pytest.raises(ValueError, match="Invalid JSON Schema"):
            DataSchema(json_schema=bad_schema)


def test_boolean_schema_validation_error() -> None:
    """Cover lines 80-86 in flow.py: validate_meta_schema boolean exception path."""
    with patch("jsonschema.Draft7Validator.check_schema") as mock_check:
        # Mock an error with a path
        error = SchemaError("Boolean schema invalid")
        error.path = deque(["nested", "path"])
        mock_check.side_effect = error

        # We pass a boolean, which triggers lines 74-86
        with pytest.raises(ValueError, match=r"Invalid JSON Schema at '/nested/path': Boolean schema invalid"):
            DataSchema(json_schema=True)
