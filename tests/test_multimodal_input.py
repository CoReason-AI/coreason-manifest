import pytest
from coreason_manifest.definitions.message import ContentPart, MultiModalInput
from coreason_manifest.definitions.session import Interaction
from uuid import uuid4

def test_content_part_instantiation() -> None:
    # Test strict instantiation
    part = ContentPart(text="Hello", file_ids=["file-123"], mime_type="text/plain")
    assert part.text == "Hello"
    assert part.file_ids == ["file-123"]
    assert part.mime_type == "text/plain"

    # Test defaults
    part = ContentPart()
    assert part.text is None
    assert part.file_ids == []
    assert part.mime_type is None

    # Test immutability
    with pytest.raises(Exception): # ValidationError or FrozenInstanceError
        part.text = "New Text" # type: ignore

def test_multimodal_input_instantiation() -> None:
    part = ContentPart(text="Check this file", file_ids=["file-1"])
    input_obj = MultiModalInput(parts=[part])
    assert len(input_obj.parts) == 1
    assert input_obj.parts[0].text == "Check this file"

    # Test immutability
    with pytest.raises(Exception):
        input_obj.parts = [] # type: ignore

def test_interaction_with_multimodal_input() -> None:
    part = ContentPart(text="Here is the report", file_ids=["f-999"])
    mm_input = MultiModalInput(parts=[part])

    interaction = Interaction(
        input=mm_input,
        output={"response": "Acknowledged"},
    )

    assert isinstance(interaction.input, MultiModalInput)
    assert interaction.input.parts[0].file_ids == ["f-999"]

    # Verify JSON serialization
    json_str = interaction.to_json()
    assert "f-999" in json_str
    assert "Here is the report" in json_str

def test_interaction_backward_compatibility() -> None:
    # Test with Dict
    interaction = Interaction(
        input={"text": "legacy input"},
        output={"response": "ok"},
    )

    assert isinstance(interaction.input, dict)
    assert interaction.input["text"] == "legacy input"

    json_str = interaction.to_json()
    assert "legacy input" in json_str
