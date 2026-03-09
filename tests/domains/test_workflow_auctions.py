# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import pytest
from pydantic import TypeAdapter, ValidationError

from coreason_manifest.workflow.auctions import TaskAward


def test_task_award_escrow_invalid() -> None:
    payload = {
        "task_id": "test_task",
        "awarded_syndicate": {"did:web:agent_1": 100},
        "cleared_price_magnitude": 100,
        "escrow": {
            "escrow_locked_magnitude": 150,
            "release_condition_metric": "quality_score > 0.9",
            "refund_target_node_id": "did:web:org_wallet_1",
        },
    }
    with pytest.raises(ValidationError, match=r"Escrow locked amount cannot exceed the total cleared price"):
        TypeAdapter(TaskAward).validate_python(payload)
