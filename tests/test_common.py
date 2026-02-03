# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from pydantic import AnyUrl

from coreason_manifest.common import CoReasonBaseModel, StrictUri, ToolRiskLevel


class CommonTestModel(CoReasonBaseModel):
    """Test model for verifying common.py primitives in isolation."""

    uri: StrictUri
    risk: ToolRiskLevel


def test_common_primitives_isolation() -> None:
    """Verify that common.py components work in isolation without other dependencies."""
    # Instantiate using the primitives
    model = CommonTestModel(
        uri=AnyUrl("https://example.com/api/v1"),
        risk=ToolRiskLevel.SAFE
    )

    # Verify StrictUri serialization to string
    assert str(model.uri) == "https://example.com/api/v1"

    # Verify Enum behavior
    assert model.risk == "safe"
    assert model.risk == ToolRiskLevel.SAFE

    # Verify serialization via CoReasonBaseModel.dump()
    dumped = model.dump()
    assert dumped["uri"] == "https://example.com/api/v1"
    assert dumped["risk"] == "safe"

    # Verify serialization via CoReasonBaseModel.to_json()
    json_output = model.to_json()
    assert '"risk":"safe"' in json_output.replace(" ", "")
    assert '"uri":"https://example.com/api/v1"' in json_output.replace(" ", "")
