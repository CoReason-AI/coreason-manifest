import pytest
from coreason_manifest.spec.ontology import GuardrailViolationEvent
from datetime import datetime


def test_guardrail_violation_event_instantiation():
    """Tests the basic instantiation and validation of GuardrailViolationEvent."""
    event = GuardrailViolationEvent(
        violation_id="viol_123",
        status_code=403,
        violation_type="pii_leak",
        violation_details={"field": "ssn", "action": "blocked"},
    )
    assert event.violation_id == "viol_123"
    assert event.status_code == 403
    assert event.violation_type == "pii_leak"
    assert event.violation_details["field"] == "ssn"
    assert isinstance(event.timestamp, datetime)


def test_guardrail_violation_event_json_isomorphism():
    """Tests that the event correctly serializes and deserializes."""
    event = GuardrailViolationEvent(
        violation_id="viol_456",
        status_code=422,
        violation_type="input_validation_failed",
        violation_details={"error": "invalid format"},
    )
    json_data = event.model_dump_json()
    rehydrated = GuardrailViolationEvent.model_validate_json(json_data)
    assert rehydrated.violation_id == event.violation_id
    assert rehydrated.status_code == event.status_code
    assert rehydrated.violation_details == event.violation_details
