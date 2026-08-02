import pytest

from coreason_manifest.utils.algebra import _validate_ssrf_safety


def test_ssrf_safety_valid_domains():
    """Test that valid non-IP domains are allowed."""
    assert _validate_ssrf_safety("http://google.com") == "http://google.com"
    assert _validate_ssrf_safety("https://api.github.com/v3") == "https://api.github.com/v3"
    assert _validate_ssrf_safety("http://127.0.0.1.nip.io") == "http://127.0.0.1.nip.io"


def test_ssrf_safety_invalid_ips():
    """Test that loopback, metadata, and non-standard IP representations are blocked."""

    invalid_urls = [
        "http://127.0.0.1",
        "http://127.1",  # short IP
        "http://2130706433",  # decimal IP
        "http://0x7f.0.0.1",  # hex IP
        "http://0177.0.0.1",  # octal IP
        "http://169.254.169.254",  # AWS metadata
        "http://[::1]",  # IPv6 loopback
        "http://localhost",  # localhost explicit block
        "http://localhost.localdomain",
    ]

    for url in invalid_urls:
        with pytest.raises(ValueError, match="SSRF Security Violation:"):
            _validate_ssrf_safety(url)
