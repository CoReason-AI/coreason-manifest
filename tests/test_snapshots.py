from pydantic import TypeAdapter
from syrupy.assertion import SnapshotAssertion

from coreason_manifest.state import EpisodicTraceMemory
from coreason_manifest.telemetry import CustodyRecord
from coreason_manifest.workflow import WorkflowEnvelope


def test_epistemic_ledger_snapshot(snapshot: SnapshotAssertion) -> None:
    payload = {
        "trace_id": "trace_1",
        "node_id": "did:web:node_1",
        "parent_hash": "hash1",
        "merkle_root": "hash2",
        "events": [
            {
                "type": "belief_update",
                "event_id": "evt_1",
                "timestamp": 1700000000.0,
                "source_node_id": "did:web:node_1",
                "payload": {
                    "semantic_node": {
                        "node_id": "did:web:node_1",
                        "label": "Person",
                        "scope": "tenant",
                        "text_chunk": "John Doe",
                        "provenance": {
                            "extracted_by": "did:web:agent_1",
                            "source_event_id": "evt_0",
                            "multimodal_anchor": {"bounding_box": [10.5, 20.0, 100.5, 200.0], "block_type": "figure"},
                        },
                    },
                    "semantic_edge": {
                        "edge_id": "edge_1",
                        "subject_node_id": "did:web:node_1",
                        "object_node_id": "did:web:node_2",
                        "confidence_score": 0.85,
                        "predicate": "WORKS_FOR",
                    },
                },
            }
        ],
    }
    ledger = TypeAdapter(EpisodicTraceMemory).validate_python(payload)
    assert snapshot == ledger.model_dump_json(by_alias=True, exclude_none=True)


def test_custody_record_snapshot(snapshot: SnapshotAssertion) -> None:
    payload = {
        "record_id": "rec_1",
        "source_node_id": "did:web:node_1",
        "applied_policy_id": "pol_1",
        "pre_redaction_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "post_redaction_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "redaction_timestamp_unix_nano": 1700000000000000000,
    }
    record = TypeAdapter(CustodyRecord).validate_python(payload)
    assert snapshot == record.model_dump_json(by_alias=True, exclude_none=True)


def test_fractal_router_snapshot(snapshot: SnapshotAssertion) -> None:
    payload = {
        "manifest_version": "1.0.0",
        "tenant_id": "tenant_acme_corp",
        "session_id": "session_98765",
        "topology": {
            "type": "dag",
            "nodes": {
                "did:web:comp_1": {
                    "type": "composite",
                    "description": "Outer topology",
                    "topology": {
                        "type": "council",
                        "adjudicator_id": "did:web:adj_1",
                        "nodes": {"did:web:adj_1": {"type": "system", "description": "The adjudicator"}},
                        "consensus_policy": {"strategy": "debate_rounds", "max_debate_rounds": 3},
                    },
                }
            },
        },
    }
    envelope = TypeAdapter(WorkflowEnvelope).validate_python(payload)
    assert snapshot == envelope.model_dump_json(by_alias=True, exclude_none=True)
