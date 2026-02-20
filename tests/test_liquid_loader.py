import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from coreason_manifest.spec.core.flow import LinearFlow
from coreason_manifest.utils.loader import Loader

@pytest.mark.asyncio
async def test_liquid_loader_remote_ref() -> None:
    """
    Test loading markdown with remote $ref using mocked HTTP.
    """
    # 1. Manifest input with markdown and remote ref
    manifest_md = """
    Here is the manifest:
    ```json
    {
        "manifest_version": "v1",
        "flow": {
            "$ref": "https://example.com/flow.json"
        }
    }
    ```
    """

    # 2. Remote content (the ref target)
    remote_flow_json = """
    {
        "kind": "LinearFlow",
        "metadata": {
            "name": "remote-flow",
            "version": "1.0",
            "description": "remote",
            "tags": []
        },
        "sequence": [],
        "governance": null
    }
    """

    mock_client_instance = AsyncMock()
    mock_response = AsyncMock()
    mock_response.text = remote_flow_json
    mock_response.raise_for_status = MagicMock()
    mock_client_instance.get.return_value = mock_response
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None

    with patch("httpx.AsyncClient", return_value=mock_client_instance):
        manifest = await Loader.aload(manifest_md, auto_heal=True)

        assert manifest.manifest_version == "v1"
        assert isinstance(manifest.flow, LinearFlow)
        assert manifest.flow.kind == "LinearFlow"
        assert manifest.flow.metadata.name == "remote-flow"

        mock_client_instance.get.assert_called_with("https://example.com/flow.json")
