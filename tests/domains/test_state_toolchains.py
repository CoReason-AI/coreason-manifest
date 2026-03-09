import pytest
from pydantic import ValidationError

from coreason_manifest.state.toolchains import BrowserDOMState


def test_browser_dom_ssrf_rejects_cloud_metadata() -> None:
    with pytest.raises(ValidationError, match="SSRF mathematical bound"):
        BrowserDOMState(
            current_url="http://169.254.169.254/iam/credentials",
            viewport_size=(800, 600),
            dom_hash="a" * 64,
            accessibility_tree_hash="a" * 64,
        )


def test_browser_dom_ssrf_rejects_localhost_variants() -> None:
    with pytest.raises(ValidationError, match="SSRF topological"):
        BrowserDOMState(
            current_url="http://localhost:3000",
            viewport_size=(800, 600),
            dom_hash="a" * 64,
            accessibility_tree_hash="a" * 64,
        )

    with pytest.raises(ValidationError, match="SSRF mathematical bound"):
        BrowserDOMState(
            current_url="http://127.0.0.1:5432",
            viewport_size=(800, 600),
            dom_hash="a" * 64,
            accessibility_tree_hash="a" * 64,
        )


def test_browser_dom_accepts_global_routable() -> None:
    # Should not raise
    state = BrowserDOMState(
        current_url="https://github.com/coreason-ai",
        viewport_size=(800, 600),
        dom_hash="a" * 64,
        accessibility_tree_hash="a" * 64,
    )
    assert state.current_url == "https://github.com/coreason-ai"
