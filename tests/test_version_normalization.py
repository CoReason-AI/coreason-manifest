# Prosperity-3.0
import uuid
from typing import Any, Dict

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.agent import SEMVER_REGEX, AgentMetadata


def test_semver_regex_validation() -> None:
    """Test the SemVer regex strictly matches patterns."""
    import re

    pattern = re.compile(SEMVER_REGEX)

    # Valid
    assert pattern.match("1.0.0")
    assert pattern.match("v1.0.0")  # Now valid input
    assert pattern.match("V1.0.0")  # Now valid input
    assert pattern.match("0.1.0-alpha.1")
    assert pattern.match("1.0.0+build.123")

    # Invalid
    assert not pattern.match("1.0")
    assert not pattern.match("1.0.0.0")
    assert not pattern.match("abc")


def test_agent_metadata_version_normalization() -> None:
    """Test that version strings with 'v' prefix are normalized."""
    base_data: Dict[str, Any] = {
        "id": uuid.uuid4(),
        "name": "Test Agent",
        "author": "Test Author",
        "created_at": "2023-10-27T10:00:00Z",
    }

    # Case 1: Standard SemVer
    data1 = base_data.copy()
    data1["version"] = "1.0.0"
    model1 = AgentMetadata(**data1)
    assert model1.version == "1.0.0"

    # Case 2: Version with 'v' prefix
    data2 = base_data.copy()
    data2["version"] = "v1.2.3"
    model2 = AgentMetadata(**data2)
    assert model2.version == "1.2.3"  # Normalized

    # Case 3: Version with 'V' prefix
    data3 = base_data.copy()
    data3["version"] = "V2.0.0-rc.1"
    model3 = AgentMetadata(**data3)
    assert model3.version == "2.0.0-rc.1"  # Normalized

    # Case 4: Invalid Version
    data4 = base_data.copy()
    data4["version"] = "invalid"
    with pytest.raises(ValidationError):
        AgentMetadata(**data4)

    # Case 5: Invalid Version (partial)
    data5 = base_data.copy()
    data5["version"] = "1.0"
    with pytest.raises(ValidationError):
        AgentMetadata(**data5)
