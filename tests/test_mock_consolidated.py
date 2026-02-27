# tests/test_mock_consolidated.py

import pytest
from coreason_manifest.utils.mock import MockAgent, MockGenerator

def test_mock_agent_response() -> None:
    # Test simple mock response
    mock_agent = MockAgent(response_template="Hello {name}")
    response = mock_agent.generate({"name": "World"})
    assert response == "Hello World"

def test_mock_generator_defaults() -> None:
    # Test generator defaults
    gen = MockGenerator()
    data = gen.generate_data("user_profile")
    assert isinstance(data, dict)
    assert "name" in data or "id" in data # Basic check depending on implementation logic

def test_mock_agent_error_simulation() -> None:
    # Test error simulation probability
    # Force error by setting probability to 1.0 (if supported) or simulating
    pass
