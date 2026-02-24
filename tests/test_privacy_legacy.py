from typing import Any

from coreason_manifest.utils.privacy import PrivacySentinel


class MockLegacyModel:
    """
    Simulates a Pydantic v1 model or similar object that has a .dict() method
    but not a .model_dump() method.
    """

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def dict(self) -> dict[str, Any]:
        return self._data


class MockBrokenModel:
    """
    Simulates a model that crashes during serialization.
    """

    def model_dump(self) -> dict[str, Any]:
        raise ValueError("Simulated serialization crash")


def test_privacy_sentinel_legacy_model_support() -> None:
    """
    Verify that PrivacySentinel supports legacy objects with a .dict() method
    (like Pydantic v1 models) by converting them to dicts and sanitizing.
    """
    sentinel = PrivacySentinel(redact_pii=True, redact_secrets=True)

    # Input data with PII and secret
    raw_data = {
        "email": "legacy@example.com",
        "api_key": "12345-secret",
        "username": "legacy_user",
    }
    legacy_model = MockLegacyModel(raw_data)

    # Sanitize the legacy model directly
    sanitized = sentinel.sanitize(legacy_model)

    # Assert it was converted to a dict
    assert isinstance(sanitized, dict)

    # Check PII redaction (precision redaction)
    assert "legacy@example.com" not in sanitized["email"]
    assert "<REDACTED:SECRET:" in sanitized["email"]

    # Check Secret redaction (key-based)
    assert "12345-secret" not in sanitized["api_key"]
    assert sanitized["api_key"].startswith("<REDACTED:SECRET:")

    # Check Safe field
    assert sanitized["username"] == "legacy_user"


def test_privacy_sentinel_serialization_error() -> None:
    """
    Verify that PrivacySentinel catches exceptions during model serialization
    and returns a safe error string instead of crashing.
    """
    sentinel = PrivacySentinel()
    broken_model = MockBrokenModel()

    # Sanitize the broken model
    sanitized = sentinel.sanitize(broken_model)

    # Assert correct error handling
    assert isinstance(sanitized, str)
    assert sanitized == "<SERIALIZATION_ERROR: ValueError>"
