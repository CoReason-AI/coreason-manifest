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

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.identity import (
    AccessScope,
    ContextField,
    IdentityRequirement,
)
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    RecipeDefinition,
    RecipeInterface,
    RecipeStatus,
    TaskSequence,
)


def test_identity_requirement_defaults() -> None:
    """Test default values for IdentityRequirement."""
    req = IdentityRequirement()
    assert req.min_scope == AccessScope.AUTHENTICATED
    assert req.required_roles == []
    assert req.required_permissions == []
    assert req.inject_user_profile is False
    assert req.inject_locale_info is True
    assert req.anonymize_pii is True


def test_identity_requirement_custom() -> None:
    """Test custom values for IdentityRequirement."""
    req = IdentityRequirement(
        min_scope=AccessScope.ADMIN,
        required_roles=["finance_admin", "auditor"],
        required_permissions=["view:report", "approve:budget"],
        inject_user_profile=True,
        inject_locale_info=False,
        anonymize_pii=False,
    )

    assert req.min_scope == AccessScope.ADMIN
    assert req.required_roles == ["finance_admin", "auditor"]
    assert req.required_permissions == ["view:report", "approve:budget"]
    assert req.inject_user_profile is True
    assert req.inject_locale_info is False
    assert req.anonymize_pii is False


def test_identity_requirement_enums() -> None:
    """Test AccessScope and ContextField enums."""
    assert AccessScope.PUBLIC.value == "public"
    assert AccessScope.AUTHENTICATED.value == "authenticated"
    assert ContextField.USER_ID.value == "user_id"
    assert ContextField.ROLES.value == "roles"


def test_identity_requirement_immutability() -> None:
    """Test that IdentityRequirement is frozen."""
    req = IdentityRequirement()
    with pytest.raises(ValidationError):
        req.min_scope = AccessScope.PUBLIC  # type: ignore[misc]


def test_recipe_definition_with_identity() -> None:
    """Test RecipeDefinition with identity field."""
    # Create a minimal valid recipe
    metadata = ManifestMetadata(name="Test Recipe", version="1.0.0")

    identity = IdentityRequirement(
        min_scope=AccessScope.INTERNAL,
        required_roles=["engineer"],
    )

    interface = RecipeInterface()
    # Create a minimal valid topology
    topology = TaskSequence(steps=[AgentNode(id="step1", agent_ref="agent-1")]).to_graph()

    recipe = RecipeDefinition(
        metadata=metadata,
        interface=interface,
        topology=topology,
        identity=identity,
        status=RecipeStatus.DRAFT
    )

    assert recipe.identity is not None
    assert recipe.identity.min_scope == AccessScope.INTERNAL
    assert recipe.identity.required_roles == ["engineer"]


def test_recipe_definition_without_identity() -> None:
    """Test RecipeDefinition without identity field (it is optional)."""
    metadata = ManifestMetadata(name="Test Recipe", version="1.0.0")

    interface = RecipeInterface()
    topology = TaskSequence(steps=[AgentNode(id="step1", agent_ref="agent-1")]).to_graph()

    recipe = RecipeDefinition(
        metadata=metadata,
        interface=interface,
        topology=topology,
        status=RecipeStatus.DRAFT
    )

    assert recipe.identity is None
