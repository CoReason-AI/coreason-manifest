import pytest

from coreason_manifest.utils.algebra import _validate_ssrf_safety


def test_validate_ssrf_safety_bypasses() -> None:
    # Valid urls
    assert _validate_ssrf_safety("http://example.com") == "http://example.com"
    assert _validate_ssrf_safety("http://8.8.8.8") == "http://8.8.8.8"

    # Blocked URLs due to SSRF
    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety("http://127.0.0.1")

    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety("http://localhost")

    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety("http://2130706433")

    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety("http://0x7f000001")

    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety("http://0177.0000.0000.0001")

    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety("http://127.1")

    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety("http://[::1]")
