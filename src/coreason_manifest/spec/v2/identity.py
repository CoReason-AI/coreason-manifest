# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from enum import StrEnum

from pydantic import ConfigDict, Field

from coreason_manifest.spec.common_base import CoReasonBaseModel


class AccessScope(StrEnum):
    """Broad permission scopes (Harvested from Coreason-Identity)."""

    PUBLIC = "public"  # No auth required
    AUTHENTICATED = "authenticated"  # Any logged-in user
    INTERNAL = "internal"  # Employee/Staff only
    ADMIN = "admin"  # Tenant Administrators


class ContextField(StrEnum):
    """Standard user context fields available for injection."""

    USER_ID = "user_id"
    EMAIL = "email"
    FULL_NAME = "full_name"
    TIMEZONE = "timezone"
    LOCALE = "locale"
    TENANT_ID = "tenant_id"
    ROLES = "roles"
    PERMISSIONS = "permissions"


class IdentityRequirement(CoReasonBaseModel):
    """RBAC and Context Injection rules for a Recipe."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    # 1. Access Control (Who can run this?)
    min_scope: AccessScope = Field(
        AccessScope.AUTHENTICATED, description="Minimum authentication level required to execute this recipe."
    )
    required_roles: list[str] = Field(
        default_factory=list, description="List of mandatory roles (OR logic). User must have at least one."
    )
    required_permissions: list[str] = Field(
        default_factory=list, description="List of specific permission strings (AND logic). User must have all."
    )

    # 2. Context Injection (What does the agent see?)
    inject_user_profile: bool = Field(False, description="If True, injects name, email, and ID into the context.")
    inject_locale_info: bool = Field(True, description="If True, injects timezone and locale/language preference.")

    # 3. Privacy
    anonymize_pii: bool = Field(
        True,
        description="If True, the runtime replaces real names/emails with hashes or aliases before sending to LLM.",
    )
