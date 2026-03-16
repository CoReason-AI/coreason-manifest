# Copyright (c) 2026 CoReason, Inc.
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

from coreason_manifest.spec.ontology import BrowserDOMState


def test_ssrf_safety_http() -> None:
    with pytest.raises(ValidationError, match="Invalid hostname in HTTP URI"):
        BrowserDOMState(
            current_url="http:///169.254.169.254",
            viewport_size=(800, 600),
            dom_hash="a" * 64,
            accessibility_tree_hash="b" * 64,
        )


def test_ssrf_safety_https() -> None:
    with pytest.raises(ValidationError, match="Invalid hostname in HTTP URI"):
        BrowserDOMState(
            current_url="https:///127.0.0.1",
            viewport_size=(800, 600),
            dom_hash="a" * 64,
            accessibility_tree_hash="b" * 64,
        )
