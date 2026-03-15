from typing import ClassVar, Any
from coreason_manifest.spec.ontology import (
    DefeasibleCascadeEvent,
    System2RemediationIntent,
)
from coreason_manifest.utils.algebra import reduce_ledger_to_active_state


def test_reduce_ledger_to_active_state_empty() -> None:
    class MockLedger:
        history: ClassVar[list[Any]] = []
        active_cascades: ClassVar[list[Any]] = []
        active_rollbacks: ClassVar[list[Any]] = []

    result = reduce_ledger_to_active_state(MockLedger())  # type: ignore
    assert result == []


def test_reduce_ledger_to_active_state_filters_quarantined_events() -> None:
    event1 = System2RemediationIntent(
        fault_id="fault-1", target_node_id="did:web:node-1", failing_pointers=["/a"], remediation_prompt="prompt"
    )
    object.__setattr__(event1, "event_id", "e1")

    event2 = System2RemediationIntent(
        fault_id="fault-2", target_node_id="did:web:node-2", failing_pointers=["/b"], remediation_prompt="prompt"
    )
    object.__setattr__(event2, "event_id", "e2")

    cascade = DefeasibleCascadeEvent(
        cascade_id="c1", propagated_decay_factor=0.5, root_falsified_event_id="e1", quarantined_event_ids=["e2"] # type: ignore
    )
    object.__setattr__(cascade, "quarantined_event_ids", ["e2"])

    class MockLedger:
        history: ClassVar[list[Any]] = [event1, event2]
        active_cascades: ClassVar[list[Any]] = [cascade]
        active_rollbacks: ClassVar[list[Any]] = []

    result = reduce_ledger_to_active_state(MockLedger())  # type: ignore
    assert result == []


def test_reduce_ledger_to_active_state_filters_invalidated_nodes() -> None:
    event1 = System2RemediationIntent(
        fault_id="fault-1", target_node_id="did:web:node-1", failing_pointers=["/a"], remediation_prompt="prompt"
    )
    object.__setattr__(event1, "event_id", "e1")
    object.__setattr__(event1, "source_node_id", "invalid_node")

    event2 = System2RemediationIntent(
        fault_id="fault-2", target_node_id="did:web:node-2", failing_pointers=["/b"], remediation_prompt="prompt"
    )
    object.__setattr__(event2, "event_id", "e2")
    object.__setattr__(event2, "source_node_id", "valid_node")

    class MockRollback:
        target_event_id: ClassVar[str] = "target_event"
        invalidated_node_ids: ClassVar[set[str]] = {"invalid_node"}

    class MockLedger:
        history: ClassVar[list[Any]] = [event1, event2]
        active_cascades: ClassVar[list[Any]] = []
        active_rollbacks: ClassVar[list[Any]] = [MockRollback()]

    result = reduce_ledger_to_active_state(MockLedger())  # type: ignore
    assert len(result) == 1
    assert result[0].event_id == "e2"
