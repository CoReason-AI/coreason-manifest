# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

"""Governance logic for V2 Manifests."""

from coreason_manifest.governance import (
    ComplianceReport,
    GovernanceConfig,
    check_compliance,
)
from coreason_manifest.v2.spec.definitions import ManifestV2


def check_compliance_v2(manifest: ManifestV2, config: GovernanceConfig) -> ComplianceReport:
    """Enforce policy on V2 Manifest before compilation.

    Delegates to the main governance implementation.

    Args:
        manifest: The V2 manifest to check.
        config: The governance policy configuration.

    Returns:
        A ComplianceReport detailing violations.
    """
    return check_compliance(manifest, config)
