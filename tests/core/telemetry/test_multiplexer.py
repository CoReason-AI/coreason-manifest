import asyncio
import json

import pytest

from coreason_manifest.core.telemetry.multiplexer import AsyncSSEMultiplexer
from coreason_manifest.core.telemetry.stream import (
    StreamCloseEnvelope,
    StreamDeltaEnvelope,
    StreamThoughtEnvelope,
)


@pytest.mark.asyncio
async def test_sse_multiplexer_push_and_stream() -> None:
    multiplexer = AsyncSSEMultiplexer()

    # Push a few packets
    await multiplexer.push(StreamDeltaEnvelope(op="delta", p="hello", timestamp=1.0))
    await multiplexer.push(StreamThoughtEnvelope(op="thought", p="thinking...", timestamp=2.0))
    await multiplexer.push(StreamCloseEnvelope(op="close", timestamp=3.0))

    generator = multiplexer.stream_sse()

    # Read first packet
    sse_1 = await anext(generator)
    assert sse_1.startswith("data: ")
    assert sse_1.endswith("\n\n")
    data_1 = json.loads(sse_1[6:-2])
    assert data_1["op"] == "delta"
    assert data_1["p"] == "hello"
    assert data_1["timestamp"] == 1.0

    # Read second packet
    sse_2 = await anext(generator)
    data_2 = json.loads(sse_2[6:-2])
    assert data_2["op"] == "thought"
    assert data_2["p"] == "thinking..."
    assert data_2["timestamp"] == 2.0

    # Read close packet
    sse_3 = await anext(generator)
    data_3 = json.loads(sse_3[6:-2])
    assert data_3["op"] == "close"
    assert data_3["p"] is None
    assert data_3["timestamp"] == 3.0

    # The generator should now be exhausted
    with pytest.raises(StopAsyncIteration):
        await anext(generator)


@pytest.mark.asyncio
async def test_sse_multiplexer_queue_initialization() -> None:
    multiplexer = AsyncSSEMultiplexer()
    assert multiplexer._queue is None

    queue = await multiplexer._get_queue()
    assert isinstance(queue, asyncio.Queue)
    assert queue.maxsize == 250
