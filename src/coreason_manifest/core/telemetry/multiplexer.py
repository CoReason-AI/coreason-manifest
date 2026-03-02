import asyncio
from collections.abc import AsyncGenerator

from coreason_manifest.core.telemetry.stream import StreamCloseEnvelope, StreamPacket


class AsyncSSEMultiplexer:
    """
    A thread-safe buffer using asyncio.Queue to handle LLM backpressure
    and multiplex stream packets into Server-Sent Events (SSE).
    """

    def __init__(self) -> None:
        """Initialize instance."""
        self._queue: asyncio.Queue[StreamPacket] | None = None

    async def _get_queue(self) -> asyncio.Queue[StreamPacket]:
        if self._queue is None:
            self._queue = asyncio.Queue(maxsize=250)
        return self._queue

    async def push(self, packet: StreamPacket) -> None:
        """Queue incoming telemetry packets onto internal memory buffer bounds."""
        queue = await self._get_queue()
        await queue.put(packet)

    async def stream_sse(self) -> AsyncGenerator[str, None]:
        """Yield continuous Server-Sent Events consuming internal buffers."""
        queue = await self._get_queue()
        while True:
            packet = await queue.get()

            try:
                # Use model_dump_json directly, formatting as SSE
                yield f"data: {packet.model_dump_json()}\n\n"
            finally:
                queue.task_done()

            if isinstance(packet, StreamCloseEnvelope):
                break
