import pytest

from coreason_manifest.utils.algebra import _validate_ssrf_safety


def test_ssrf_validation_blocks_localhost() -> None:
    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety("http://localhost:8080/admin")

    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety("http://127.0.0.1/admin")

    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety("http://[::1]/admin")


def test_ssrf_validation_allows_valid_urls() -> None:
    assert _validate_ssrf_safety("https://api.github.com/v1") == "https://api.github.com/v1"
    assert _validate_ssrf_safety("https://8.8.8.8/dns") == "https://8.8.8.8/dns"


def test_ssrf_validation_bypasses() -> None:
    # octal IP for 127.0.0.1
    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety("http://0177.0.0.1/")

    # integer IP for 127.0.0.1 (2130706433)
    with pytest.raises(ValueError, match="SSRF Security Violation"):
        _validate_ssrf_safety("http://2130706433/")
