import pytest

from coreason_manifest.core.common.presentation import AdaptiveUIContract
from coreason_manifest.core.telemetry.multiplexer import AsyncSSEMultiplexer
from coreason_manifest.core.telemetry.stream import (
    StreamCloseEnvelope,
    StreamDeltaEnvelope,
    StreamThoughtEnvelope,
    StreamUIEnvelope,
)


@pytest.mark.asyncio
async def test_sse_multiplexer() -> None:
    multiplexer = AsyncSSEMultiplexer()

    delta = StreamDeltaEnvelope(op="delta", p="test", timestamp=1.0)
    thought = StreamThoughtEnvelope(op="thought", p="I am thinking", timestamp=1.5)

    ui_contract = AdaptiveUIContract(
        widget_id="test_widget",
        props_schema={"type": "object"},
        props_mapping={},
        events=[],
    )
    ui_envelope = StreamUIEnvelope(op="ui_mount", p=ui_contract, timestamp=1.8)

    close = StreamCloseEnvelope(op="close", p=None, timestamp=2.0)

    await multiplexer.push(delta)
    await multiplexer.push(thought)
    await multiplexer.push(ui_envelope)
    await multiplexer.push(close)

    stream = multiplexer.stream_sse()

    item1 = await anext(stream)
    assert item1.startswith("data: {")
    assert "delta" in item1

    item2 = await anext(stream)
    assert item2.startswith("data: {")
    assert "thought" in item2
    assert "I am thinking" in item2

    item3 = await anext(stream)
    assert item3.startswith("data: {")
    assert "ui_mount" in item3
    assert "test_widget" in item3

    item4 = await anext(stream)
    assert item4.startswith("data: {")
    assert "close" in item4

    with pytest.raises(StopAsyncIteration):
        await anext(stream)
