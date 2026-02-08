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
    """Broad permission scopes."""

    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    INTERNAL = "internal"
    ADMIN = "admin"


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
    """RBAC and Context Injection rules."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    # 1. Access Control (Who can run this?)
    min_scope: AccessScope = Field(AccessScope.AUTHENTICATED, description="Minimum auth level required.")
    required_roles: list[str] = Field(default_factory=list, description="List of mandatory roles (OR logic).")
    required_permissions: list[str] = Field(
        default_factory=list,
        description="List of specific permission strings (AND logic).",
    )

    # 2. Context Injection (What does the agent see?)
    # If True, the runtime injects these values into the System Prompt preamble.
    inject_user_profile: bool = Field(False, description="Inject name, email, and ID.")
    inject_locale_info: bool = Field(True, description="Inject timezone and locale/language.")

    # 3. Privacy
    anonymize_pii: bool = Field(
        True,
        description="If True, replaces real names/emails with hashes/aliases in the prompt.",
    )
