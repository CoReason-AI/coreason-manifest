
import pytest

from coreason_manifest.definitions.interfaces import IResponseHandler, IStreamEmitter
from coreason_manifest.definitions.presentation import CitationBlock, PresentationEvent


class MockStreamEmitter:
    def __init__(self) -> None:
        self._active = True

    async def emit_chunk(self, content: str) -> None:
        if not self._active:
            raise RuntimeError("Stream is closed")

    async def close(self) -> None:
        self._active = False


class MockResponseHandler:
    async def emit_event(self, event: PresentationEvent) -> None:
        pass

    async def emit_thought(self, content: str) -> None:
        pass

    async def emit_citation(self, citation: CitationBlock) -> None:
        pass

    async def create_text_stream(self, name: str) -> IStreamEmitter:
        return MockStreamEmitter()

    async def complete(self) -> None:
        pass


@pytest.mark.asyncio
async def test_stream_emitter_protocol() -> None:
    emitter = MockStreamEmitter()
    # Runtime checkable
    assert isinstance(emitter, IStreamEmitter)
    await emitter.emit_chunk("chunk")
    await emitter.close()
    with pytest.raises(RuntimeError):
        await emitter.emit_chunk("chunk")


@pytest.mark.asyncio
async def test_response_handler_protocol() -> None:
    handler = MockResponseHandler()
    # Runtime checkable
    assert isinstance(handler, IResponseHandler)

    stream = await handler.create_text_stream("test")
    assert isinstance(stream, IStreamEmitter)
    await stream.emit_chunk("hello")
    await stream.close()
