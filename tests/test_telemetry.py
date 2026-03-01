
import pytest

from coreason_manifest.core.telemetry.multiplexer import AsyncSSEMultiplexer
from coreason_manifest.core.telemetry.stream import StreamCloseEnvelope, StreamDeltaEnvelope


@pytest.mark.asyncio
async def test_sse_multiplexer() -> None:
    multiplexer = AsyncSSEMultiplexer()

    delta = StreamDeltaEnvelope(op="delta", p="test", timestamp=1.0)
    close = StreamCloseEnvelope(op="close", p=None, timestamp=2.0)

    await multiplexer.push(delta)
    await multiplexer.push(close)

    stream = multiplexer.stream_sse()

    item1 = await anext(stream)
    assert item1.startswith("data: {")
    assert "delta" in item1

    item2 = await anext(stream)
    assert item2.startswith("data: {")
    assert "close" in item2

    with pytest.raises(StopAsyncIteration):
        await anext(stream)
