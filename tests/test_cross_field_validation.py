import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.nodes import HumanNode, SwarmNode
from coreason_manifest.spec.core.tools import ToolCapability


def test_human_node_shadow_mode_requirements():
    """
    If interaction_mode is 'shadow', shadow_timeout_seconds is required.
    """
    with pytest.raises(ValidationError) as excinfo:
        HumanNode(
            id="h1",
            type="human",
            prompt="Shadow?",
            interaction_mode="shadow",
            timeout_seconds=None
            # Missing shadow_timeout_seconds
        )
    # Check that one of the errors contains our message
    errors = excinfo.value.errors()
    assert any("HumanNode in 'shadow' mode requires 'shadow_timeout_seconds'" in e["msg"] for e in errors)

def test_human_node_shadow_mode_valid():
    h = HumanNode(
        id="h1",
        type="human",
        prompt="Shadow?",
        interaction_mode="shadow",
        shadow_timeout_seconds=60,
        timeout_seconds=None
    )
    assert h.interaction_mode == "shadow"
    assert h.shadow_timeout_seconds == 60

def test_human_node_blocking_mode_invalid_field():
    """
    If interaction_mode is 'blocking', shadow_timeout_seconds should not be set.
    """
    with pytest.raises(ValidationError) as excinfo:
        HumanNode(
            id="h1",
            type="human",
            prompt="Block?",
            interaction_mode="blocking",
            shadow_timeout_seconds=60,
            timeout_seconds=10
        )
    errors = excinfo.value.errors()
    assert any("HumanNode in 'blocking' mode must not have 'shadow_timeout_seconds'" in e["msg"] for e in errors)

def test_swarm_node_summarize_requires_aggregator():
    """
    If reducer_function is 'summarize', aggregator_model is required.
    """
    with pytest.raises(ValidationError) as excinfo:
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
    errors = excinfo.value.errors()
    assert any("SwarmNode with reducer='summarize' requires an 'aggregator_model'" in e["msg"] for e in errors)

def test_tool_critical_description():
    """
    If risk_level is 'critical', description is required.
    """
    with pytest.raises(ValidationError) as excinfo:
        ToolCapability(
            name="nuke_db",
            type="capability",
            risk_level="critical",
            # Missing description
        )
    errors = excinfo.value.errors()
    assert any("is Critical but lacks a description" in e["msg"] for e in errors)
