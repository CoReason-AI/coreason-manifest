import pytest
from pydantic import BaseModel, Field, ValidationError

from coreason_manifest.presentation.remediation import generate_correction_prompt


class MockStrictSchema(BaseModel):
    name: str = Field(min_length=5)
    age: int


def test_generate_correction_prompt_translation() -> None:
    # Test invalid type (triggering the else branch "Invalid structural payload")
    try:
        MockStrictSchema(name="Bob", age="not_an_int")
        pytest.fail("Should have raised ValidationError")
    except ValidationError as e:
        prompt = generate_correction_prompt(error=e, target_node_id="did:web:node-1", fault_id="fault-001")

        assert prompt.fault_id == "fault-001"
        assert prompt.target_node_id == "did:web:node-1"

        # Both pointers should be mapped
        assert "/name" in prompt.failing_pointers
        assert "/age" in prompt.failing_pointers

        # Verify deterministic error injection
        assert "CRITICAL CONTRACT BREACH" in prompt.remediation_prompt
        assert "'/name'" in prompt.remediation_prompt
        assert "'/age'" in prompt.remediation_prompt

    # Test missing field (triggering the "missing" branch)
    try:
        MockStrictSchema(name="Bob")
        pytest.fail("Should have raised ValidationError")
    except ValidationError as e:
        prompt = generate_correction_prompt(error=e, target_node_id="did:web:node-1", fault_id="fault-002")

        assert "/age" in prompt.failing_pointers
        assert "is completely missing" in prompt.remediation_prompt
