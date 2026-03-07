# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import pytest
from pydantic import ValidationError

from coreason_manifest.oversight.audit import MechanisticAuditContract


def test_mechanistic_audit_contract_valid() -> None:
    contract = MechanisticAuditContract(
        trigger_conditions=["on_tool_call", "on_belief_update"],
        target_layers=[12, 14, 16],
        max_features_per_layer=64,
        require_zk_commitments=True,
    )
    assert "on_tool_call" in contract.trigger_conditions
    assert contract.target_layers == [12, 14, 16]
    assert contract.max_features_per_layer == 64
    assert contract.require_zk_commitments is True


def test_mechanistic_audit_contract_invalid_empty_triggers() -> None:
    with pytest.raises(ValidationError, match="List should have at least 1 item after validation"):
        MechanisticAuditContract(
            trigger_conditions=[],
            target_layers=[12, 14],
            max_features_per_layer=64,
        )


def test_mechanistic_audit_contract_invalid_trigger_literal() -> None:
    with pytest.raises(ValidationError):
        MechanisticAuditContract(
            trigger_conditions=["on_thought"],  # type: ignore
            target_layers=[12, 14],
            max_features_per_layer=64,
        )


def test_mechanistic_audit_contract_invalid_empty_layers() -> None:
    with pytest.raises(ValidationError, match="List should have at least 1 item after validation"):
        MechanisticAuditContract(
            trigger_conditions=["on_tool_call"],
            target_layers=[],
            max_features_per_layer=64,
        )


def test_mechanistic_audit_contract_invalid_features() -> None:
    with pytest.raises(ValidationError, match="Input should be greater than 0"):
        MechanisticAuditContract(
            trigger_conditions=["on_tool_call"],
            target_layers=[12],
            max_features_per_layer=0,
        )
