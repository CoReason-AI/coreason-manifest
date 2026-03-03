import asyncio
from datetime import UTC, datetime

import pytest

from coreason_manifest.core.state.events import EpistemicAnchor, EpistemicEvent, EventType
from coreason_manifest.core.state.ledger import EpistemicLedger
from coreason_manifest.core.workflow.bidding import CapabilityRouter
from coreason_manifest.core.workflow.blackboard import BlackboardBroker
from coreason_manifest.core.workflow.nodes.etl.auditor import AuditorNode
from coreason_manifest.core.workflow.nodes.etl.semantic import SemanticNode


@pytest.fixture
def ledger() -> EpistemicLedger:
    return EpistemicLedger()


@pytest.fixture
def broker(ledger: EpistemicLedger) -> BlackboardBroker:
    return BlackboardBroker(ledger=ledger)


@pytest.fixture
def mock_event() -> EpistemicEvent:
    return EpistemicEvent(
        event_id="test-event-1",
        timestamp=datetime.now(UTC),
        context_envelope={"hardware_cluster": "cluster-1", "agent_signature": "agent-1", "prompt_version": "v1"},
        event_type=EventType.STRUCTURAL_PARSED,
        payload={"data": "test"},
        epistemic_anchor=EpistemicAnchor(parent_event_id=None, spatial_coordinates=None),
    )


@pytest.mark.asyncio
async def test_pub_sub_routing(broker: BlackboardBroker, mock_event: EpistemicEvent) -> None:
    """
    Test 1: Prove that publishing a structural event triggers the SemanticNode's queue
    but not the AuditorNode's queue.
    """
    semantic_queue: asyncio.Queue[EpistemicEvent] = asyncio.Queue()
    auditor_queue: asyncio.Queue[EpistemicEvent] = asyncio.Queue()

    await broker.subscribe(str(EventType.STRUCTURAL_PARSED), semantic_queue)
    await broker.subscribe(str(EventType.SEMANTIC_EXTRACTED), auditor_queue)

    await broker.publish(mock_event)

    assert not semantic_queue.empty()
    assert auditor_queue.empty()

    event_received = await semantic_queue.get()
    assert event_received.event_id == mock_event.event_id


@pytest.mark.asyncio
async def test_thundering_herd(broker: BlackboardBroker, mock_event: EpistemicEvent) -> None:
    """
    Test 2: Prove EXACTLY ONE node gets the lock when 3 attempt simultaneously.
    """
    async def claim_attempt(agent_signature: str) -> bool:
        return await broker.claim_task(mock_event.event_id, agent_signature=agent_signature, ttl_seconds=30)

    results = await asyncio.gather(
        claim_attempt("agent-1"),
        claim_attempt("agent-2"),
        claim_attempt("agent-3"),
    )

    # Exactly one True, the rest False
    assert results.count(True) == 1
    assert results.count(False) == 2


@pytest.mark.asyncio
async def test_ttl_fault_recovery(broker: BlackboardBroker, mock_event: EpistemicEvent) -> None:
    """
    Test 3: Prove that if a lock's TTL expires, another node can successfully claim it.
    """
    # Claim with a 0-second TTL (expires immediately)
    claimed_1 = await broker.claim_task(mock_event.event_id, agent_signature="node-A", ttl_seconds=0)
    assert claimed_1 is True

    # Sleep slightly to ensure time passes
    await asyncio.sleep(0.01)

    # Node B tries to claim
    claimed_2 = await broker.claim_task(mock_event.event_id, agent_signature="node-B", ttl_seconds=30)
    assert claimed_2 is True

    # Node C tries to claim before TTL
    claimed_3 = await broker.claim_task(mock_event.event_id, agent_signature="node-C", ttl_seconds=30)
    assert claimed_3 is False


@pytest.mark.asyncio
async def test_capability_routing(mock_event: EpistemicEvent) -> None:
    """
    Test capability routing fallback (SuspenseEnvelope).
    """
    router = CapabilityRouter(suspense_threshold=0.95)

    # SemanticNode scores 0.9 for STRUCTURAL_PARSED
    # Since 0.9 < 0.95, it should fallback to suspense envelope
    semantic_node = SemanticNode(
        id="semantic_1",
        hardware_profile="nlp-cluster-1",
        profile="profile_1", operational_policy=None
    )

    result = await router.offer_task(mock_event, [semantic_node])

    # Should be a StreamSuspenseEnvelope
    assert type(result).__name__ == "StreamSuspenseEnvelope"
    assert result.trace_id == f"suspense-{mock_event.event_id}"
