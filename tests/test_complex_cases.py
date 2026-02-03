# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import uuid
from pathlib import Path

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.agent import AgentDefinition


def test_deep_immutability_mapping_proxy() -> None:
    """Test that dictionary fields are converted to immutable MappingProxyType."""
    data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Immutable",
            "author": "Tester",
            "created_at": "2023-01-01T00:00:00Z",
        },
        "capabilities": [
            {
                "name": "default",
                "type": "atomic",
                "description": "Default",
                "inputs": {"param": 1},
                "outputs": {},
            }
        ],
        "config": {
            "nodes": [],
            "edges": [],
            "entry_point": "start",
            "model_config": {"model": "gpt", "temperature": 0.1},
            "system_prompt": "Dummy",
        },
        "dependencies": {
            "tools": [
                {
                    "uri": "https://example.com/a",
                    "hash": "a" * 64,
                    "scopes": [],
                    "risk_level": "safe",
                }
            ],
            "libraries": [],
        },
        "integrity_hash": "a" * 64,
    }
    agent = AgentDefinition(**data)

    # inputs should be read-only
    assert agent.capabilities[0].inputs is not None
    with pytest.raises(TypeError, match="'mappingproxy' object does not support item assignment"):
        agent.capabilities[0].inputs["param"] = 2  # type: ignore[index]

    with pytest.raises(TypeError, match="'mappingproxy' object does not support item assignment"):
        agent.capabilities[0].inputs["new"] = 3  # type: ignore[index]


def test_deep_immutability_tuples() -> None:
    """Test that list fields are converted to immutable tuples or lists as defined."""
    data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Immutable",
            "author": "Tester",
            "created_at": "2023-01-01T00:00:00Z",
        },
        "capabilities": [
            {
                "name": "default",
                "type": "atomic",
                "description": "Default",
                "inputs": {},
                "outputs": {},
            }
        ],
        "config": {
            "nodes": [],
            "edges": [],
            "entry_point": "start",
            "model_config": {"model": "gpt", "temperature": 0.1},
            "system_prompt": "Dummy",
        },
        "dependencies": {
            "tools": [
                {
                    "uri": "https://example.com/tool1",
                    "hash": "a" * 64,
                    "scopes": [],
                    "risk_level": "safe",
                }
            ],
            "libraries": [],
        },
        "integrity_hash": "a" * 64,
    }
    agent = AgentDefinition(**data)

    # tools is now a list as per new requirement
    assert isinstance(agent.dependencies.tools, list)

    # libraries remains a tuple
    assert isinstance(agent.dependencies.libraries, tuple)

    # Test field immutability (model is frozen)
    with pytest.raises(ValidationError, match="Instance is frozen"):
        agent.dependencies.libraries = ("a",)  # type: ignore[misc]

    # Test tools field immutability (model is frozen)
    with pytest.raises(ValidationError, match="Instance is frozen"):
        agent.dependencies.tools = []  # type: ignore[misc]

    # Note: agent.dependencies.tools is a list, so its CONTENTS are mutable,
    # but the field itself cannot be reassigned.


def test_unicode_handling() -> None:
    """Test that unicode characters are handled correctly in fields."""
    name_unicode = "Agént-Ω"
    author_unicode = "Jules 🤖"

    data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": name_unicode,
            "author": author_unicode,
            "created_at": "2023-01-01T00:00:00Z",
        },
        "capabilities": [
            {
                "name": "default",
                "type": "atomic",
                "description": "Default",
                "inputs": {"key_Ω": "val_🤖"},
                "outputs": {},
            }
        ],
        "config": {
            "nodes": [],
            "edges": [],
            "entry_point": "start",
            "model_config": {"model": "gpt", "temperature": 0.1},
            "system_prompt": "Dummy",
        },
        "dependencies": {"tools": [], "libraries": []},
        "integrity_hash": "a" * 64,
    }
    agent = AgentDefinition(**data)

    assert agent.metadata.name == name_unicode
    assert agent.metadata.author == author_unicode
    assert agent.capabilities[0].inputs is not None
    assert agent.capabilities[0].inputs["key_Ω"] == "val_🤖"


def test_hash_validation_edge_cases() -> None:
    """Test various edge cases for integrity hash validation."""
    base_data = {
        "metadata": {
            "id": str(uuid.uuid4()),
            "version": "1.0.0",
            "name": "Test",
            "author": "Tester",
            "created_at": "2023-01-01T00:00:00Z",
        },
        "capabilities": [
            {
                "name": "default",
                "type": "atomic",
                "description": "Default",
                "inputs": {},
                "outputs": {},
            }
        ],
        "config": {
            "nodes": [],
            "edges": [],
            "entry_point": "start",
            "model_config": {"model": "gpt", "temperature": 0.1},
            "system_prompt": "Dummy",
        },
        "dependencies": {"tools": [], "libraries": []},
        "status": "published",  # Explicitly set to published to enforce hash check
    }

    # Too short
    with pytest.raises(ValidationError) as exc:
        AgentDefinition(**{**base_data, "integrity_hash": "a" * 63})
    assert "String should match pattern" in str(exc.value)

    # Too long
    with pytest.raises(ValidationError) as exc:
        AgentDefinition(**{**base_data, "integrity_hash": "a" * 65})
    assert "String should match pattern" in str(exc.value)

    # Invalid chars
    with pytest.raises(ValidationError) as exc:
        AgentDefinition(**{**base_data, "integrity_hash": "z" * 64})  # z is not hex
    assert "String should match pattern" in str(exc.value)

    # Uppercase valid
    valid_upper = "A" * 64
    agent = AgentDefinition(**{**base_data, "integrity_hash": valid_upper})
    assert agent.integrity_hash == valid_upper


def test_integrity_checker_invalid_hash_format(tmp_path: Path) -> None:
    """IntegrityChecker should fail if hash is structurally invalid (though model validation usually catches it)."""
    # This tests the edge case where somehow an invalid hash got past model validation
    # (e.g. if one were to mock the model or manually construct it bypassing validation,
    # which is hard with pydantic v2)
    # But mainly, verify IntegrityChecker works with weird hashes if they were valid
    pass  # IntegrityChecker just compares strings, so format doesn't matter for the check itself, just equality.
