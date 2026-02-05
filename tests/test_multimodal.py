import pytest
from pydantic import ValidationError

from coreason_manifest import (
    AttachedFile,
    ContentPart,
    Interaction,
    MultiModalInput,
)


def test_strict_serialization() -> None:
    """Test serialization of MultiModalInput."""
    file = AttachedFile(id="file-123", mime_type="application/pdf")
    part = ContentPart(text="Analyze this", attachments=[file])
    mm_input = MultiModalInput(parts=[part])

    dumped = mm_input.dump()

    assert dumped == {
        "parts": [{"text": "Analyze this", "attachments": [{"id": "file-123", "mime_type": "application/pdf"}]}]
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


def test_edge_case_empty_parts() -> None:
    """Test MultiModalInput with empty parts list."""
    mm_input = MultiModalInput(parts=[])
    assert mm_input.parts == []
    assert mm_input.dump() == {"parts": []}


def test_edge_case_empty_content_part() -> None:
    """Test ContentPart with no text and no attachments."""
    part = ContentPart()
    assert part.text is None
    assert part.attachments == []
    # CoReasonBaseModel excludes none, so it should be empty dict if no attachments
    # But attachments has a default factory of list, so it will be present as []?
    # Let's check serialization behavior. CoReasonBaseModel uses exclude_none=True.
    # Empty list is not None.
    assert part.dump() == {"attachments": []}


def test_edge_case_huge_text() -> None:
    """Test ContentPart with a very large string."""
    huge_text = "a" * 10_000
    part = ContentPart(text=huge_text)
    assert part.text == huge_text


def test_edge_case_many_attachments() -> None:
    """Test ContentPart with many attachments."""
    attachments = [AttachedFile(id=f"id-{i}") for i in range(100)]
    part = ContentPart(attachments=attachments)
    assert len(part.attachments) == 100
    assert part.attachments[99].id == "id-99"


def test_complex_mixed_content() -> None:
    """Test MultiModalInput with mixed content parts."""
    img = AttachedFile(id="img-1")
    doc = AttachedFile(id="doc-1")

    p1 = ContentPart(text="Look at this:")
    p2 = ContentPart(attachments=[img])
    p3 = ContentPart(text="and this document", attachments=[doc])

    mm_input = MultiModalInput(parts=[p1, p2, p3])

    assert len(mm_input.parts) == 3
    assert mm_input.parts[0].text == "Look at this:"
    assert len(mm_input.parts[0].attachments) == 0
    assert mm_input.parts[1].text is None
    assert mm_input.parts[1].attachments[0].id == "img-1"
    assert mm_input.parts[2].text == "and this document"
    assert mm_input.parts[2].attachments[0].id == "doc-1"
