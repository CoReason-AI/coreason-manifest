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
from pydantic import HttpUrl, ValidationError

from coreason_manifest.spec.ontology import HTTPTransportProfile, SSETransportProfile


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:8080/admin",
        "http://127.0.0.1/",
        "http://[::1]/",
        "http://169.254.169.254/",
        "http://192.168.1.1/",
        "http://localtest.me/",
        "http:127.0.0.1",
        "http:/127.0.0.1",
    ],
)
def test_http_transport_profile_ssrf(url: str) -> None:
    with pytest.raises(ValidationError, match=r"SSRF (topological violation|restricted IP) detected"):
        HTTPTransportProfile(uri=HttpUrl(url))


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:8080/admin",
        "http://127.0.0.1/",
        "http://[::1]/",
        "http://169.254.169.254/",
        "http://192.168.1.1/",
        "http://localtest.me/",
        "http:127.0.0.1",
        "http:/127.0.0.1",
    ],
)
def test_sse_transport_profile_ssrf(url: str) -> None:
    with pytest.raises(ValidationError, match=r"SSRF (topological violation|restricted IP) detected"):
        SSETransportProfile(uri=HttpUrl(url))


@pytest.mark.parametrize(
    "url",
    [
        "https://www.example.com/",
        "http://1.1.1.1/",
    ],
)
def test_http_transport_profile_valid(url: str) -> None:
    profile = HTTPTransportProfile(uri=HttpUrl(url))
    assert str(profile.uri) == url


@pytest.mark.parametrize(
    "url",
    [
        "https://www.example.com/",
        "http://1.1.1.1/",
    ],
)
def test_sse_transport_profile_valid(url: str) -> None:
    profile = SSETransportProfile(uri=HttpUrl(url))
    assert str(profile.uri) == url
