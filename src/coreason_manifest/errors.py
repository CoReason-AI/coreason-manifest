# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

"""Custom exceptions for Coreason Manifest."""


class SecurityViolationError(ValueError):
    """Raised when a file reference escapes the allowed jail directory."""

    pass


class ManifestRecursionError(RecursionError):
    """Raised when a circular dependency is detected in manifest imports."""

    pass
