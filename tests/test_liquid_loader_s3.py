import pytest
from unittest.mock import MagicMock, patch
from coreason_manifest.utils.loader import Loader
from coreason_manifest.spec.core.flow import LinearFlow

@pytest.mark.asyncio
async def test_loader_s3() -> None:
    """
    Test loading from s3:// URI.
    """
    s3_uri = "s3://my-bucket/manifest.json"
    manifest_content = """
    {
        "manifest_version": "v1",
        "flow": {
            "kind": "LinearFlow",
            "metadata": {
                "name": "s3-flow",
                "version": "1.0",
                "description": "s3",
                "tags": []
            },
            "sequence": []
        }
    }
    """

    # Mock boto3
    mock_boto3 = MagicMock()
    mock_s3_client = MagicMock()
    mock_boto3.client.return_value = mock_s3_client

    mock_response = {"Body": MagicMock()}
    mock_response["Body"].read.return_value = manifest_content.encode("utf-8")
    mock_s3_client.get_object.return_value = mock_response

    with patch.dict("sys.modules", {"boto3": mock_boto3}):
        manifest = await Loader.aload(s3_uri)

        assert isinstance(manifest.flow, LinearFlow)
        assert manifest.flow.kind == "LinearFlow"
        assert manifest.flow.metadata.name == "s3-flow"

        mock_s3_client.get_object.assert_called_with(Bucket="my-bucket", Key="manifest.json")
