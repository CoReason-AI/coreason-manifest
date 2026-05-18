import pytest
from pydantic import AnyUrl

from coreason_manifest.utils.algebra import _validate_ssrf_safety


def test_validate_ssrf_safety() -> None:
    # Valid global URLs
    assert _validate_ssrf_safety(AnyUrl("https://example.com"))
    assert _validate_ssrf_safety(AnyUrl("http://8.8.8.8"))

    # Invalid private/local URLs
    with pytest.raises(ValueError, match="SSRF"):
        _validate_ssrf_safety(AnyUrl("http://127.0.0.1/api"))
    with pytest.raises(ValueError, match="SSRF"):
        _validate_ssrf_safety(AnyUrl("http://169.254.169.254/latest/meta-data/"))
    with pytest.raises(ValueError, match="SSRF"):
        _validate_ssrf_safety(AnyUrl("http://10.0.0.1/"))

    with pytest.raises(ValueError, match="SSRF"):
        _validate_ssrf_safety(AnyUrl("http://localhost/api"))
    with pytest.raises(ValueError, match="SSRF"):
        _validate_ssrf_safety(AnyUrl("http://localhost.localdomain/api"))
