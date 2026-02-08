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
        metadata=metadata, interface=interface, topology=topology, identity=identity, status=RecipeStatus.DRAFT
    )

    assert recipe.identity is not None
    assert recipe.identity.min_scope == AccessScope.INTERNAL
    assert recipe.identity.required_roles == ["engineer"]


def test_recipe_definition_without_identity() -> None:
    """Test RecipeDefinition without identity field (it is optional)."""
    metadata = ManifestMetadata(name="Test Recipe", version="1.0.0")

    interface = RecipeInterface()
    topology = TaskSequence(steps=[AgentNode(id="step1", agent_ref="agent-1")]).to_graph()

    recipe = RecipeDefinition(metadata=metadata, interface=interface, topology=topology, status=RecipeStatus.DRAFT)

    assert recipe.identity is None


# --- Edge Case Tests ---


def test_identity_edge_cases_empty_lists() -> None:
    """Test empty lists for roles and permissions (Edge Case 1)."""
    req = IdentityRequirement(
        required_roles=[],
        required_permissions=[],
    )
    assert req.required_roles == []
    assert req.required_permissions == []


def test_identity_edge_cases_boolean_flags() -> None:
    """Test all boolean combinations (Edge Case 2)."""
    # All True
    req_true = IdentityRequirement(
        inject_user_profile=True,
        inject_locale_info=True,
        anonymize_pii=True,
    )
    assert req_true.inject_user_profile is True
    assert req_true.inject_locale_info is True
    assert req_true.anonymize_pii is True

    # All False
    req_false = IdentityRequirement(
        inject_user_profile=False,
        inject_locale_info=False,
        anonymize_pii=False,
    )
    assert req_false.inject_user_profile is False
    assert req_false.inject_locale_info is False
    assert req_false.anonymize_pii is False


def test_identity_edge_cases_invalid_enum() -> None:
    """Test validation error for invalid enum value (Edge Case 3)."""
    with pytest.raises(ValidationError):
        IdentityRequirement(min_scope="invalid_scope")


def test_identity_edge_cases_duplicate_roles() -> None:
    """Test that duplicate roles are preserved (list semantic) but valid (Edge Case 4)."""
    req = IdentityRequirement(
        required_roles=["admin", "admin"],
        required_permissions=["read", "read"],
    )
    # Pydantic doesn't deduplicate lists by default
    assert req.required_roles == ["admin", "admin"]
    assert req.required_permissions == ["read", "read"]


def test_identity_edge_cases_invalid_list_type() -> None:
    """Test validation error when passing a string instead of a list (Edge Case 5)."""
    with pytest.raises(ValidationError):
        # Mypy would catch this, but we test runtime validation
        IdentityRequirement(required_roles="admin")


def test_identity_edge_cases_extra_fields() -> None:
    """Test that extra fields are forbidden (Edge Case 6)."""
    with pytest.raises(ValidationError):
        IdentityRequirement(extra_field="should_fail")  # type: ignore[call-arg]


# --- Complex Case Tests ---


def test_complex_finance_admin_scenario() -> None:
    """Test a complex 'Finance Admin' scenario with specific permissions (Complex Case 1)."""
    identity = IdentityRequirement(
        min_scope=AccessScope.ADMIN,
        required_roles=["finance_admin", "cfo"],
        required_permissions=["read:financials", "generate:report", "approve:budget"],
        inject_user_profile=True,
        inject_locale_info=True,
        anonymize_pii=False,  # Need real name for signatures
    )

    assert identity.min_scope == AccessScope.ADMIN
    assert "finance_admin" in identity.required_roles
    assert "cfo" in identity.required_roles
    assert len(identity.required_permissions) == 3
    assert identity.anonymize_pii is False


def test_complex_public_bot_scenario() -> None:
    """Test a minimal 'Public Bot' scenario (Complex Case 2)."""
    identity = IdentityRequirement(
        min_scope=AccessScope.PUBLIC,
        required_roles=[],
        required_permissions=[],
        inject_user_profile=False,
        inject_locale_info=True,  # Still need locale for language
        anonymize_pii=True,
    )

    assert identity.min_scope == AccessScope.PUBLIC
    assert not identity.required_roles
    assert not identity.required_permissions
    assert identity.inject_user_profile is False
    assert identity.inject_locale_info is True


def test_complex_recipe_integration() -> None:
    """Test full integration of a complex identity into a Recipe (Complex Case 3)."""
    metadata = ManifestMetadata(name="Secure Workflow", version="2.0.0")

    identity = IdentityRequirement(
        min_scope=AccessScope.INTERNAL,
        required_roles=["engineer", "security_champion"],
        required_permissions=["deploy:prod"],
        inject_user_profile=True,
    )

    interface = RecipeInterface(inputs={"target": {"type": "string"}}, outputs={"status": {"type": "string"}})

    topology = TaskSequence(steps=[AgentNode(id="deployer", agent_ref="deploy-bot")]).to_graph()

    recipe = RecipeDefinition(
        metadata=metadata,
        interface=interface,
        topology=topology,
        identity=identity,
        status=RecipeStatus.PUBLISHED,  # Ensure it works with PUBLISHED status too
    )

    assert recipe.identity is not None
    assert recipe.identity.min_scope == AccessScope.INTERNAL
    assert recipe.identity.required_permissions == ["deploy:prod"]
    # Verify defaults didn't change unexpectedly
    assert recipe.identity.anonymize_pii is True


def test_complex_max_constraints_scenario() -> None:
    """Test a scenario where ALL fields are set to strict/non-default values (Complex Case 4)."""
    identity = IdentityRequirement(
        min_scope=AccessScope.ADMIN,
        required_roles=["superadmin", "owner", "root"],
        required_permissions=["system:reset", "system:wipe", "audit:delete"],
        inject_user_profile=True,
        inject_locale_info=False,
        anonymize_pii=False
    )

    dumped = identity.dump()
    assert dumped["min_scope"] == "admin"
    assert len(dumped["required_roles"]) == 3
    assert len(dumped["required_permissions"]) == 3
    assert dumped["inject_user_profile"] is True
    assert dumped["inject_locale_info"] is False
    assert dumped["anonymize_pii"] is False
