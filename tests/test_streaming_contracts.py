# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.common.capabilities import (
    AgentCapabilities,
    CapabilityType,
    DeliveryMode,
)


def test_contract_defaults() -> None:
    """Verify default values for streaming contract."""
    caps = AgentCapabilities()
    assert caps.type == CapabilityType.GRAPH
    assert caps.delivery_mode == DeliveryMode.REQUEST_RESPONSE
    assert caps.history_support is True


def test_explicit_configuration() -> None:
    """Verify explicit configuration of streaming contract."""
    caps = AgentCapabilities(
        type=CapabilityType.ATOMIC,
        delivery_mode=DeliveryMode.SERVER_SENT_EVENTS,
    )
    assert caps.type == CapabilityType.ATOMIC
    assert caps.delivery_mode == DeliveryMode.SERVER_SENT_EVENTS


def test_immutability() -> None:
    """Verify that the model is frozen."""
    caps = AgentCapabilities()

    with pytest.raises(ValidationError):
        caps.delivery_mode = DeliveryMode.SERVER_SENT_EVENTS  # type: ignore


def test_serialization() -> None:
    """Verify JSON serialization uses correct string values."""
    caps = AgentCapabilities(
        type=CapabilityType.ATOMIC,
        delivery_mode=DeliveryMode.SERVER_SENT_EVENTS,
    )
    data = caps.model_dump(mode="json")
    assert data["type"] == "atomic"
    assert data["delivery_mode"] == "server_sent_events"
