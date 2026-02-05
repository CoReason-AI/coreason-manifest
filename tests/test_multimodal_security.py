import pytest

from coreason_manifest import (
    AttachedFile,
    ContentPart,
    Interaction,
    MultiModalInput,
)


def test_security_massive_payload_dos() -> None:
    """Test handling of massive payloads to prevent DoS."""
    # Create a massive text string
    massive_text = "A" * 1_000_000  # 1MB string

    # Create many parts
    parts = [ContentPart(text=massive_text) for _ in range(10)]

    # This should instantiate without crashing, but we might want to see if it's too slow
    # Pydantic validates this fine, but downstream consumers need to handle it.
    # Here we just verify the model accepts it (as it's just a data container).
    mm_input = MultiModalInput(parts=parts)
    assert len(mm_input.parts) == 10
    assert len(mm_input.parts[0].text) == 1_000_000  # type: ignore


def test_security_injection_payloads() -> None:
    """Test that models accept injection strings (they are just data containers).

    The security responsibility lies with the consumer (sanitization),
    but the model itself should not execute anything.
    """
    xss_payload = "<script>alert('xss')</script>"
    sql_payload = "'; DROP TABLE users; --"

    part = ContentPart(text=xss_payload)
    assert part.text == xss_payload

    file_ref = AttachedFile(id=sql_payload)  # ID field might be vulnerable if used raw in DB
    assert file_ref.id == sql_payload


def test_security_recursion_depth() -> None:
    """Test recursion handling.

    The `Interaction` model allows `Dict[str, Any]`. Pydantic V2 is generally smart enough
    to handle recursive dictionaries in `Any` fields without crashing immediately during validation,
    unless serialization is attempted.
    """
    recursive_dict = {}
    recursive_dict["self"] = recursive_dict

    # This should NOT raise RecursionError during instantiation.
    # Note: Pydantic creates a copy, so 'is' identity check fails.
    interaction = Interaction(input=recursive_dict)
    assert isinstance(interaction.input, dict)

    # However, attempting to DUMP it should probably fail or crash with RecursionError
    with pytest.raises((ValueError, RecursionError)):
        interaction.dump()


def test_security_type_confusion() -> None:
    """Test type confusion (Smart Union Behavior).

    In Pydantic V2, `Union[MultiModalInput, str, Dict]` uses 'smart' mode.
    If a dict matches the schema of `MultiModalInput`, it WILL be coerced.
    This is generally desired for API robustness but can be surprising.
    """
    # A dict that looks exactly like MultiModalInput
    fake_input = {"parts": [{"text": "fake", "attachments": []}]}

    interaction = Interaction(input=fake_input)

    # Pydantic V2 coerces this to MultiModalInput because it fits the schema perfectly
    assert isinstance(interaction.input, MultiModalInput)
    assert interaction.input.parts[0].text == "fake"

    # A dict that implies MultiModalInput but fails validation (e.g. invalid type inside)
    # should fall back to Dict if possible?
    # Actually, if it matches the shape enough to try validation but fails, Pydantic might raise error
    # OR fall back to the next type in Union (Dict).

    # Let's try a dict that definitely IS NOT a MultiModalInput
    plain_dict = {"foo": "bar"}
    interaction_plain = Interaction(input=plain_dict)
    assert isinstance(interaction_plain.input, dict)
    assert interaction_plain.input == plain_dict


def test_security_unicode_normalization() -> None:
    """Test weird unicode characters."""
    weird_text = "\u202ereversed text\u202c"  # Right-to-Left Override
    part = ContentPart(text=weird_text)
    assert part.text == weird_text
