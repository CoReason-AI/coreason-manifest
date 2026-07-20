# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

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

    # Obfuscated IP addresses bypassing naive validation
    with pytest.raises(ValueError, match="SSRF"):
        _validate_ssrf_safety(AnyUrl("http://127.1/api"))
    with pytest.raises(ValueError, match="SSRF"):
        _validate_ssrf_safety(AnyUrl("http://0x7f.0.0.1/api"))
    with pytest.raises(ValueError, match="SSRF"):
        _validate_ssrf_safety(AnyUrl("http://0177.0.0.1/api"))
