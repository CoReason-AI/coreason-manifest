# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from coreason_manifest.spec.ontology import BrowserDOMState


def test_browser_dom_state_valid_topology() -> None:
    state = BrowserDOMState(
        current_url="https://1.1.1.1",
        viewport_size=(1920, 1080),
        dom_hash="a" * 64,
        accessibility_tree_hash="b" * 64,
    )
    assert state.current_url == "https://1.1.1.1"


def test_browser_dom_state_accepts_any_url() -> None:
    """After SSRF purge, the data plane accepts any structurally valid URL."""
    state = BrowserDOMState(
        current_url="http://localhost:8080/admin",
        viewport_size=(1024, 768),
        dom_hash="a" * 64,
        accessibility_tree_hash="b" * 64,
    )
    assert state.current_url == "http://localhost:8080/admin"
