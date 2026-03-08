# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from pydantic import TypeAdapter

from coreason_manifest.oversight.intervention import (
    AnyInterventionPayload,
    ConstitutionalAmendmentProposal,
)


def test_constitutional_amendment_proposal_routing() -> None:
    payload_data = {
        "type": "constitutional_amendment",
        "drift_event_id": "drift_123",
        "proposed_patch": {"op": "replace", "path": "/rules/3/threshold", "value": 0.8},
        "justification": "The prior rule threshold of 0.9 caused loop condition #42 in state tracking.",
    }

    adapter: TypeAdapter[AnyInterventionPayload] = TypeAdapter(AnyInterventionPayload)
    parsed_payload = adapter.validate_python(payload_data)

    assert isinstance(parsed_payload, ConstitutionalAmendmentProposal)
    assert parsed_payload.drift_event_id == "drift_123"
    assert parsed_payload.proposed_patch == {"op": "replace", "path": "/rules/3/threshold", "value": 0.8}
    assert (
        parsed_payload.justification == "The prior rule threshold of 0.9 caused loop condition #42 in state tracking."
    )
