from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest.models import (
    AgentDefinition,
)


def test_agent_auth_validation() -> None:
    """Test that agents requiring auth must have user_context injected."""

    base_data = {
        "metadata": {
            "id": str(uuid4()),
            "version": "1.0.0",
            "name": "AuthAgent",
            "author": "Tester",
            "created_at": datetime.now(timezone.utc),
            "requires_auth": True,
        },
        "interface": {
            "inputs": {},
            "outputs": {},
            "injected_params": [],  # Missing user_context
        },
        "topology": {"steps": [], "model_config": {"model": "gpt-4", "temperature": 0.5}},
        "dependencies": {"tools": [], "libraries": []},
        "integrity_hash": "a" * 64,
    }

    # Should fail
    with pytest.raises(
        ValidationError, match="Agent requires authentication but 'user_context' is not an injected parameter"
    ):
        AgentDefinition(**base_data)

    # Should pass
    base_data["interface"]["injected_params"] = ["user_context"]
    agent = AgentDefinition(**base_data)
    assert agent.metadata.requires_auth is True
    assert "user_context" in agent.interface.injected_params
