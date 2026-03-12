import pytest
from pydantic import ValidationError

from coreason_manifest.utils.algebra import validate_payload
from coreason_manifest.spec.ontology import DynamicLayoutManifest

def test_validate_payload_invalid_step() -> None:
    with pytest.raises(ValueError, match=r"FATAL: Unknown step 'invalid_step'. Valid steps:"):
        validate_payload("invalid_step", b"{}")

def test_validate_payload_invalid_json() -> None:
    with pytest.raises(ValidationError):
        validate_payload("step8_vision", b'{"invalid": "data"}')
