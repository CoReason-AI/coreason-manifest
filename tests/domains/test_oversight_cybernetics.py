import pytest
from pydantic import TypeAdapter

from coreason_manifest.oversight.cybernetics import CyberneticControlLoop


def test_cybernetic_control_loop_serialization_determinism() -> None:
    payload = {
        "homeostatic_deviation_vector": {"byzantine_fault_detected": False, "latency": 150},
        "adjudication_rationale": "Latency within bounds.",
        "regulatory_intervention_action": {
            "type": "request",
            "target_node_id": "did:web:node1",
            "context_summary": "High latency",
            "proposed_action": {"action": "scale_up"},
            "adjudication_deadline": 1678886400.0,
        },
    }

    adapter = TypeAdapter(CyberneticControlLoop)
    obj = adapter.validate_python(payload)

    # Assert deterministic serialization
    serialized = adapter.dump_python(obj, mode="json")
    assert serialized["homeostatic_deviation_vector"]["byzantine_fault_detected"] is False
    assert serialized["homeostatic_deviation_vector"]["latency"] == 150
    assert serialized["adjudication_rationale"] == "Latency within bounds."
    assert serialized["regulatory_intervention_action"]["type"] == "request"
    assert serialized["regulatory_intervention_action"]["target_node_id"] == "did:web:node1"


def test_byzantine_fault_requires_severe_intervention() -> None:
    payload = {
        "homeostatic_deviation_vector": {"byzantine_fault_detected": True, "loss": 0.5},
        "adjudication_rationale": "Byzantine fault detected in cluster.",
        "regulatory_intervention_action": {
            "type": "request",
            "target_node_id": "did:web:node1",
            "context_summary": "System anomaly",
            "proposed_action": {"action": "log"},
            "adjudication_deadline": 1678886400.0,
        },
    }

    adapter = TypeAdapter(CyberneticControlLoop)
    with pytest.raises(
        ValueError,
        match=r"ECONOMICS_VIOLATION: A Byzantine fault requires a severe regulatory intervention "
        r"\(quarantine, slash_stake, or circuit_breaker\).",
    ):
        adapter.validate_python(payload)


def test_byzantine_fault_accepts_severe_intervention() -> None:
    payload = {
        "homeostatic_deviation_vector": {"byzantine_fault_detected": True, "critical_drift": 0.99},
        "adjudication_rationale": "Byzantine fault detected; severing malicious node.",
        "regulatory_intervention_action": {
            "type": "quarantine",
            "target_node_id": "did:web:malicious-node",
            "reason": "Cryptographic signature mismatch.",
        },
    }

    adapter = TypeAdapter(CyberneticControlLoop)
    # This must NOT raise a ValueError
    obj = adapter.validate_python(payload)

    # Assert structural integrity was maintained
    assert obj.regulatory_intervention_action.type == "quarantine"
    assert getattr(obj.regulatory_intervention_action, "target_node_id", None) == "did:web:malicious-node"
