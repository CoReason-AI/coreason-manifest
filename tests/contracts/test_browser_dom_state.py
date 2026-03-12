import pytest
from pydantic import ValidationError

from coreason_manifest.spec.ontology import BrowserDOMState


def test_browser_dom_state_spatial_safety() -> None:
    """
    Validates the spatial safety boundaries of BrowserDOMState.
    It verifies that globally routable URLs pass, while explicit Bogon space
    (localhost, private IPs) and advanced SSRF bypass techniques (hex, octal, integer representations)
    are strictly quarantined.
    """

    # 1. Valid, globally routable URL should pass
    state = BrowserDOMState(
        current_url="https://www.example.com",
        viewport_size=(1920, 1080),
        dom_hash="a" * 64,
        accessibility_tree_hash="b" * 64,
    )
    assert state.current_url == "https://www.example.com"

    # 2. Blocked schemes (file://) and explicit localhost
    with pytest.raises(ValidationError, match="SSRF topological violation detected"):
        BrowserDOMState(
            current_url="file:///etc/passwd",
            viewport_size=(1920, 1080),
            dom_hash="a" * 64,
            accessibility_tree_hash="b" * 64,
        )

    with pytest.raises(ValidationError, match="SSRF topological violation detected"):
        BrowserDOMState(
            current_url="http://localhost:8080/admin",
            viewport_size=(1920, 1080),
            dom_hash="a" * 64,
            accessibility_tree_hash="b" * 64,
        )

    # 3. Standard Private IPs and SSRF bypass variants (hex, integer, octal, IPv6)
    invalid_ips = [
        "http://127.0.0.1/",  # Standard private
        "http://192.168.1.1/",  # Standard private
        "http://169.254.169.254/",  # Cloud metadata
        "http://0x7f000001/",  # 127.0.0.1 in Hex
        "http://2130706433/",  # 127.0.0.1 in Integer
        "http://0177.0.0.1/",  # 127.0.0.1 in Octal format
        "http://0x7f.0.0.1/",  # 127.0.0.1 in mixed Hex/Decimal
        "http://[::1]/",  # IPv6 loopback
    ]

    for url in invalid_ips:
        with pytest.raises(ValidationError, match="SSRF mathematical bound violation detected"):
            BrowserDOMState(
                current_url=url,
                viewport_size=(1920, 1080),
                dom_hash="a" * 64,
                accessibility_tree_hash="b" * 64,
            )
