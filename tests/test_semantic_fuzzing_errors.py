import pytest
from pydantic import ValidationError

from coreason_manifest.state.semantic import VectorEmbedding
from coreason_manifest.tooling.environments import ActionSpace


def test_vector_embedding_dimensionality_mismatch():
    with pytest.raises(ValidationError) as exc_info:
        VectorEmbedding(vector=[1.0, 2.0], dimensionality=3, model_name="test")
    assert "does not match vector length" in str(exc_info.value)


def test_action_space_duplicate_tools():
    tool = {
        "tool_name": "dup_tool",
        "description": "test",
        "input_schema": {},
        "side_effects": {"is_idempotent": True, "mutates_state": False},
        "permissions": {"network_access": False, "file_system_read_only": True},
    }
    with pytest.raises(ValidationError) as exc_info:
        ActionSpace(action_space_id="test", native_tools=[tool, tool], mcp_servers=[])
    assert "Tool names within an ActionSpace must be strictly unique" in str(exc_info.value)
