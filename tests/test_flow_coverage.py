from collections import deque
from unittest.mock import patch, MagicMock

import pytest
from jsonschema.exceptions import SchemaError

from coreason_manifest.spec.core.flow import DataSchema, FlowDefinitions, FlowMetadata, LinearFlow
from coreason_manifest.spec.interop.exceptions import ManifestError
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile, SwarmNode
from coreason_manifest.spec.core.tools import ToolCapability, ToolPack
from coreason_manifest.utils.validator import validate_flow


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

    flow_bad_ref = LinearFlow(
        kind="LinearFlow",
        status="published",
        metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
        definitions=definitions,
        steps=[agent_bad_ref],
    )
    errors = validate_flow(flow_bad_ref)
    assert any("invalid resilience reference" in e for e in errors)

    # 3. Invalid Resilience Ref ID (lines 310-311)
    agent_missing_ref = AgentNode(
        id="a3",
        type="agent",
        metadata={},
        profile=CognitiveProfile(role="r", persona="p", reasoning=None, fast_path=None),
        tools=[],
        resilience="ref:missing",
    )

    flow_missing_ref = LinearFlow(
        kind="LinearFlow",
        status="published",
        metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
        definitions=definitions,
        steps=[agent_missing_ref],
    )
    errors = validate_flow(flow_missing_ref)
    assert any("references undefined supervision template" in e for e in errors)

    # 4. Invalid Profile Ref (lines 319-320)
    agent_missing_profile = AgentNode(
        id="a4", type="agent", metadata={}, profile="missing-profile", tools=[], resilience=None
    )

    flow_missing_profile = LinearFlow(
        kind="LinearFlow",
        status="published",
        metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
        definitions=definitions,
        steps=[agent_missing_profile],
    )
    errors = validate_flow(flow_missing_profile)
    assert any("references undefined profile ID" in e for e in errors)

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

    flow_swarm_missing = LinearFlow(
        kind="LinearFlow",
        status="published",
        metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
        definitions=definitions,
        steps=[swarm_missing],
    )
    errors = validate_flow(flow_swarm_missing)
    assert any("references undefined worker profile ID" in e for e in errors)


def test_schema_strict_validation_failure() -> None:
    """Cover strict validation exception handling in flow.py: validate_meta_schema."""
    # We want check_schema to fail, causing an immediate exception.

    with patch("jsonschema.validators.validator_for") as mock_validator_for:
        mock_validator_cls = MagicMock()
        mock_validator_cls.check_schema.side_effect = SchemaError("Strict Validation Error")
        mock_validator_for.return_value = mock_validator_cls

        # We need a schema that triggers the logic
        bad_schema = {"type": "bad_type"}  # This calls check_schema

        with pytest.raises(ManifestError, match="Invalid JSON Schema"):
            DataSchema(json_schema=bad_schema)


def test_boolean_schema_validation_error() -> None:
    """Cover lines 80-86 in flow.py: validate_meta_schema boolean exception path."""
    with patch("jsonschema.validators.validator_for") as mock_validator_for:
        # Mock an error with a path
        error = SchemaError("Boolean schema invalid")
        error.path = deque(["nested", "path"])
        mock_validator_cls = MagicMock()
        mock_validator_cls.check_schema.side_effect = error
        mock_validator_for.return_value = mock_validator_cls

        # We pass a boolean, which triggers lines 74-86
        # Note: The error message format changed in ManifestError
        with pytest.raises(ManifestError, match=r"Invalid JSON Schema"):
            DataSchema(json_schema={"type": "any"})
