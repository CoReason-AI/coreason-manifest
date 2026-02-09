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

from coreason_manifest.spec.common_base import ManifestBaseModel, StrictUri, ToolRiskLevel


class CommonTestModel(ManifestBaseModel):
    """Test model for verifying common.py primitives in isolation."""

    uri: StrictUri
    risk: ToolRiskLevel


def test_common_primitives_isolation() -> None:
    """Verify that common.py components work in isolation without other dependencies."""
    # Instantiate using the primitives
    model = CommonTestModel(uri=AnyUrl("https://example.com/api/v1"), risk=ToolRiskLevel.SAFE)

    # Verify StrictUri serialization to string
    assert str(model.uri) == "https://example.com/api/v1"

    # Verify Enum behavior
    assert model.risk.value == "safe"
    assert model.risk == ToolRiskLevel.SAFE

    # Verify serialization via ManifestBaseModel.model_dump(mode='json', by_alias=True, exclude_none=True)
    dumped = model.model_dump(mode='json', by_alias=True, exclude_none=True)
    assert dumped["uri"] == "https://example.com/api/v1"
    assert dumped["risk"] == "safe"

    # Verify serialization via ManifestBaseModel.model_dump_json(by_alias=True, exclude_none=True)
    json_output = model.model_dump_json(by_alias=True, exclude_none=True)
    assert '"risk":"safe"' in json_output.replace(" ", "")
    assert '"uri":"https://example.com/api/v1"' in json_output.replace(" ", "")
