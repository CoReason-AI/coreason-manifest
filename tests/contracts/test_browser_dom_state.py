# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import ipaddress

import hypothesis.strategies as st
import pytest
from hypothesis import given, settings
from pydantic import ValidationError

from coreason_manifest.spec.ontology import BrowserDOMState


# Isolate the Happy Path
def test_browser_dom_state_valid_topology() -> None:
    state = BrowserDOMState(
        current_url="https://www.example.com",
        viewport_size=(1920, 1080),
        dom_hash="a" * 64,
        accessibility_tree_hash="b" * 64,
    )
    assert state.current_url == "https://www.example.com"


# Parameterize Protocol/Schema violations for atomic reporting
@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "http://localhost:8080/admin",
        "http://broadcasthost/test",
        "http://something.local/",
        "http://server.internal/",
        "http://test.arpa/",
        "http://127.0.0.1.nip.io",  # Magic DNS bypass
        "http://127.0.0.1.sslip.io",
    ],
)
def test_browser_dom_state_topological_violations(url: str) -> None:
    with pytest.raises(ValidationError, match="SSRF topological violation detected"):
        BrowserDOMState(
            current_url=url, viewport_size=(1920, 1080), dom_hash="a" * 64, accessibility_tree_hash="b" * 64
        )


# Parameterize explicit IP bypass vectors
@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",  # Standard private
        "http://192.168.1.1/",  # Standard private
        "http://169.254.169.254/",  # Cloud metadata
        "http://0x7f000001/",  # 127.0.0.1 in Hex
        "http://2130706433/",  # 127.0.0.1 in Integer
        "http://0177.0.0.1/",  # 127.0.0.1 in Octal format
        "http://0x7f.0.0.1/",  # mixed Hex/Decimal
        "http://[::1]/",  # IPv6 loopback
        "http://[::ffff:127.0.0.1]/",  # IPv4-mapped IPv6 (Missing Scenario)
        "http://127.000.000.001/",  # Zero-padded (Missing Scenario)
    ],
)
def test_browser_dom_state_mathematical_bounds(url: str) -> None:
    with pytest.raises(ValidationError, match="SSRF mathematical bound violation detected"):
        BrowserDOMState(
            current_url=url, viewport_size=(1920, 1080), dom_hash="a" * 64, accessibility_tree_hash="b" * 64
        )


@given(st.ip_addresses(v=4))
@settings(max_examples=100)
def test_browser_dom_state_fuzz_ipv4_space(ip: ipaddress.IPv4Address) -> None:
    """
    AGENT INSTRUCTION: Fuzz the entire IPv4 coordinate space.
    Mathematically assert that any IP defined as private/bogon by the stdlib is quarantined.
    """
    url = f"http://{ip}/"

    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
        with pytest.raises(ValidationError, match="SSRF mathematical bound violation"):
            BrowserDOMState(
                current_url=url, viewport_size=(1024, 768), dom_hash="a" * 64, accessibility_tree_hash="b" * 64
            )
    else:
        # Publicly routable IPs must successfully project into the state
        state = BrowserDOMState(
            current_url=url, viewport_size=(1024, 768), dom_hash="a" * 64, accessibility_tree_hash="b" * 64
        )
        assert state.current_url == url
