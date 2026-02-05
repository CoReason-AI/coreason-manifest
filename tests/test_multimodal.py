import pytest
from pydantic import ValidationError

from coreason_manifest import (
    AttachedFile,
    ContentPart,
    MultiModalInput,
    Interaction,
)

def test_strict_serialization() -> None:
    """Test serialization of MultiModalInput."""
    file = AttachedFile(id="file-123", mime_type="application/pdf")
    part = ContentPart(text="Analyze this", attachments=[file])
    mm_input = MultiModalInput(parts=[part])

    dumped = mm_input.dump()

    assert dumped == {
        "parts": [
            {
                "text": "Analyze this",
                "attachments": [
                    {"id": "file-123", "mime_type": "application/pdf"}
                ]
            }
        ]
    }

def test_interaction_polymorphism_rich() -> None:
    """Test Interaction with MultiModalInput."""
    file = AttachedFile(id="f1")
    part = ContentPart(attachments=[file])
    mm_input = MultiModalInput(parts=[part])

    interaction = Interaction(input=mm_input)
    assert interaction.input == mm_input

def test_interaction_polymorphism_string() -> None:
    """Test Interaction with string input."""
    interaction = Interaction(input="Simple string")
    assert interaction.input == "Simple string"

def test_interaction_polymorphism_dict() -> None:
    """Test Interaction with dict input."""
    data = {"raw": "data", "foo": 123}
    interaction = Interaction(input=data)
    assert interaction.input == data

def test_immutability() -> None:
    """Test that models are frozen."""
    part = ContentPart(text="foo")
    mm_input = MultiModalInput(parts=[part])

    with pytest.raises(ValidationError):
        mm_input.parts = []  # type: ignore[misc]

    file = AttachedFile(id="123")
    with pytest.raises(ValidationError):
        file.id = "456"  # type: ignore[misc]

    # Test Interaction immutability
    interaction = Interaction(input="test")
    with pytest.raises(ValidationError):
        interaction.input = "new"  # type: ignore[misc]
