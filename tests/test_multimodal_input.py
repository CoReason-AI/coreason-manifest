import pytest
import json
from pydantic import ValidationError

from coreason_manifest.definitions.message import ContentPart, MultiModalInput, AttachedFile
from coreason_manifest.definitions.session import Interaction


def test_content_part_instantiation() -> None:
    # Test strict instantiation
    file_ref = AttachedFile(id="file-123", mime_type="text/plain")
    part = ContentPart(text="Hello", attachments=[file_ref])
    assert part.text == "Hello"
    assert len(part.attachments) == 1
    assert part.attachments[0].id == "file-123"
    assert part.attachments[0].mime_type == "text/plain"

    # Test defaults
    part = ContentPart()
    assert part.text is None
    assert part.attachments == []

    # Test immutability
    with pytest.raises(ValidationError):
        part.text = "New Text"  # type: ignore


def test_multimodal_input_instantiation() -> None:
    file_ref = AttachedFile(id="file-1")
    part = ContentPart(text="Check this file", attachments=[file_ref])
    input_obj = MultiModalInput(parts=[part])
    assert len(input_obj.parts) == 1
    assert input_obj.parts[0].text == "Check this file"
    assert input_obj.parts[0].attachments[0].id == "file-1"

    # Test immutability
    with pytest.raises(ValidationError):
        input_obj.parts = []  # type: ignore


def test_interaction_with_multimodal_input() -> None:
    file_ref = AttachedFile(id="f-999")
    part = ContentPart(text="Here is the report", attachments=[file_ref])
    mm_input = MultiModalInput(parts=[part])

    interaction = Interaction(
        input=mm_input,
        output={"response": "Acknowledged"},
    )

    assert isinstance(interaction.input, MultiModalInput)
    assert interaction.input.parts[0].attachments[0].id == "f-999"

    # Verify JSON serialization
    json_str = interaction.to_json()
    assert "f-999" in json_str
    assert "Here is the report" in json_str

    # Verify nested structure in JSON
    data = json.loads(json_str)
    assert data["input"]["parts"][0]["attachments"][0]["id"] == "f-999"


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
