import asyncio
from collections.abc import AsyncGenerator

from coreason_manifest.core.telemetry.stream import StreamCloseEnvelope, StreamPacket


class AsyncSSEMultiplexer:
    """
    A thread-safe buffer using asyncio.Queue to handle LLM backpressure
    and multiplex stream packets into Server-Sent Events (SSE).
    """

    def __init__(self) -> None:
        """Initialize the multiplexer ring buffer with capacity constraints."""
        self._queue: asyncio.Queue[StreamPacket] | None = None

    async def _get_queue(self) -> asyncio.Queue[StreamPacket]:
        """Retrieve or initialize the designated async queue for a specific stream subscriber."""
        if self._queue is None:
            self._queue = asyncio.Queue(maxsize=250)
        return self._queue

    async def push(self, packet: StreamPacket) -> None:
        """Broadcast telemetry envelopes synchronously across all active consumer queues."""
        queue = await self._get_queue()
        await queue.put(packet)

    async def stream_sse(self) -> AsyncGenerator[str, None]:
        """Generator that continuously yields Server-Sent Events from the multiplexer buffer."""
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
