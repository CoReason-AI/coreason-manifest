import pytest
from pydantic import HttpUrl

from coreason_manifest.utils.algebra import _validate_ssrf_safety


def test_validate_ssrf_safety_valid() -> None:
    # Valid global addresses
    url = HttpUrl("http://8.8.8.8/")
    assert _validate_ssrf_safety(url) == url

    url = HttpUrl("https://1.1.1.1/dns-query")
    assert _validate_ssrf_safety(url) == url


def test_validate_ssrf_safety_hostname_bypassed() -> None:
    # The function skips validation for non-IP hostnames because DNS resolution is air-gapped
    url = HttpUrl("http://example.com/")
    assert _validate_ssrf_safety(url) == url


def test_validate_ssrf_safety_loopback() -> None:
    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety(HttpUrl("http://127.0.0.1/"))

    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety(HttpUrl("http://localhost/"))


def test_validate_ssrf_safety_private() -> None:
    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety(HttpUrl("http://192.168.1.1/"))

    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety(HttpUrl("http://10.0.0.1/"))

    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety(HttpUrl("http://172.16.0.1/"))


def test_validate_ssrf_safety_obscure_ipv4() -> None:
    # Test integer representation of 127.0.0.1
    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety(HttpUrl("http://2130706433/"))

    # Test octal representation of 127.0.0.1
    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety(HttpUrl("http://0177.0.0.1/"))

    # Test hex representation of 127.0.0.1
    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety(HttpUrl("http://0x7f.0.0.1/"))


def test_validate_ssrf_safety_ipv6_mapped() -> None:
    # Test IPv4-mapped IPv6 address pointing to loopback
    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety(HttpUrl("http://[::ffff:127.0.0.1]/"))


def test_validate_ssrf_safety_reserved_or_link_local() -> None:
    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety(HttpUrl("http://169.254.169.254/"))

    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety(HttpUrl("http://0.0.0.0/"))
