import pytest
from typing import Any, Dict, Optional, Union
from coreason_manifest.definitions.interfaces import ResponseHandler, StreamHandle
from coreason_manifest.definitions.events import CloudEvent, GraphEvent

class MockStreamHandle:
    def __init__(self, stream_id: str):
        self._stream_id = stream_id
        self._active = True

    @property
    def stream_id(self) -> str:
        return self._stream_id

    @property
    def is_active(self) -> bool:
        return self._active

    async def write(self, chunk: str) -> None:
        if not self._active:
            raise RuntimeError("Stream is closed")

    async def close(self) -> None:
        self._active = False

    async def abort(self, reason: str) -> None:
        self._active = False

class MockResponseHandler:
    async def emit(self, event: Union[CloudEvent[Any], GraphEvent]) -> None:
        pass

    async def thought(self, content: str, status: str = "IN_PROGRESS") -> None:
        pass

    async def markdown(self, content: str) -> None:
        pass

    async def data(
        self,
        data: Dict[str, Any],
        title: Optional[str] = None,
        view_hint: str = "JSON",
    ) -> None:
        pass

    async def error(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = False,
    ) -> None:
        pass

    async def create_stream(
        self, title: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
    ) -> StreamHandle:
        return MockStreamHandle("test-stream-id")

@pytest.mark.asyncio
async def test_stream_handle_protocol():
    handle = MockStreamHandle("id")
    # Runtime checkable
    assert isinstance(handle, StreamHandle)
    assert handle.stream_id == "id"
    assert handle.is_active
    await handle.write("chunk")
    await handle.close()
    assert not handle.is_active
    with pytest.raises(RuntimeError):
        await handle.write("chunk")

@pytest.mark.asyncio
async def test_response_handler_protocol():
    handler = MockResponseHandler()
    # Not runtime checkable, so we just test method invocation
    stream = await handler.create_stream()
    assert isinstance(stream, StreamHandle)
    await stream.write("hello")
    await stream.close()
