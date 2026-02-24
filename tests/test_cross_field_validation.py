import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.nodes import SwarmNode
from coreason_manifest.spec.core.tools import ToolCapability
from coreason_manifest.spec.core.types import RiskLevel
from coreason_manifest.spec.interop.exceptions import ManifestError


def test_swarm_node_summarize_requires_aggregator() -> None:
    """
    If reducer_function is 'summarize', aggregator_model is required.
    """
    with pytest.raises(ManifestError) as excinfo:
        SwarmNode(
            id="s1",
            type="swarm",
            worker_profile="worker",
            workload_variable="items",
            distribution_strategy="sharded",
            max_concurrency=10,
            reducer_function="summarize",
            output_variable="result",
            # Missing aggregator_model
        )
    assert "SwarmNode with reducer='summarize' requires an 'aggregator_model'" in excinfo.value.fault.message


def test_tool_critical_description() -> None:
    """
    If risk_level is 'critical', description is required.
    """
    with pytest.raises(ValidationError) as excinfo:
        ToolCapability(
            name="nuke_db",
            type="capability",
            risk_level=RiskLevel.CRITICAL,
            # Missing description
        )
    errors = excinfo.value.errors()
    assert any("is Critical but lacks a description" in e["msg"] for e in errors)
