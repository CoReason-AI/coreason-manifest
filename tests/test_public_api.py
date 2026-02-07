# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest import (
    InterceptorContext,
    IRequestInterceptor,
    IResponseInterceptor,
)
from coreason_manifest.spec.interfaces.middleware import (
    InterceptorContext as InternalInterceptorContext,
)


def test_public_api_exports() -> None:
    """Verify that middleware components are exported from the top-level package."""
    assert InterceptorContext is InternalInterceptorContext
    assert isinstance(IRequestInterceptor, type)
    assert isinstance(IResponseInterceptor, type)
