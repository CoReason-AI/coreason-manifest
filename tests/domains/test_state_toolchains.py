# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import BrowserDOMState


def test_browser_dom_ssrf_rejects_cloud_metadata() -> None:
    with pytest.raises(ValidationError, match="SSRF mathematical bound"):
        BrowserDOMState(
            current_url="http://169.254.169.254/iam/credentials",
            viewport_size=(800, 600),
            dom_hash="a" * 64,
            accessibility_tree_hash="a" * 64,
        )


def test_browser_dom_ssrf_rejects_localhost_variants() -> None:
    with pytest.raises(ValidationError, match="SSRF topological"):
        BrowserDOMState(
            current_url="http://localhost:3000",
            viewport_size=(800, 600),
            dom_hash="a" * 64,
            accessibility_tree_hash="a" * 64,
        )

    with pytest.raises(ValidationError, match="SSRF mathematical bound"):
        BrowserDOMState(
            current_url="http://127.0.0.1:5432",
            viewport_size=(800, 600),
            dom_hash="a" * 64,
            accessibility_tree_hash="a" * 64,
        )


def test_browser_dom_accepts_global_routable() -> None:
    # Should not raise
    state = BrowserDOMState(
        current_url="https://github.com/coreason-ai",
        viewport_size=(800, 600),
        dom_hash="a" * 64,
        accessibility_tree_hash="a" * 64,
    )
    assert state.current_url == "https://github.com/coreason-ai"


def test_browser_dom_accepts_global_ip() -> None:
    # Coverage for line returning url after IP checks (Line 66)
    state = BrowserDOMState(
        current_url="https://8.8.8.8/search",
        viewport_size=(800, 600),
        dom_hash="a" * 64,
        accessibility_tree_hash="a" * 64,
    )
    assert state.current_url == "https://8.8.8.8/search"


def test_browser_dom_accepts_no_hostname() -> None:
    # Coverage for line returning url when there is no hostname (Line 45)
    state = BrowserDOMState(
        current_url="about:blank", viewport_size=(800, 600), dom_hash="a" * 64, accessibility_tree_hash="a" * 64
    )
    assert state.current_url == "about:blank"
