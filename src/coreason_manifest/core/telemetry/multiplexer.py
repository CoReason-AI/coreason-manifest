import asyncio
from collections.abc import AsyncGenerator

from coreason_manifest.core.telemetry.stream import StreamCloseEnvelope, StreamPacket


class AsyncSSEMultiplexer:
    """
    A thread-safe buffer using asyncio.Queue to handle LLM backpressure
    and multiplex stream packets into Server-Sent Events (SSE).
    """

    def __init__(self) -> None:
        """Initialize the multiplexer with a queue."""
        self._queue: asyncio.Queue[StreamPacket] | None = None

    async def _get_queue(self) -> asyncio.Queue[StreamPacket]:
        if self._queue is None:
            self._queue = asyncio.Queue(maxsize=250)
        return self._queue

    async def push(self, packet: StreamPacket) -> None:
        """
        Push a stream packet into the buffer with a timeout to prevent deadlock.
        """
        import contextlib

        queue = await self._get_queue()
        with contextlib.suppress(TimeoutError):
            # If the queue is full and timing out, we drop the packet to prevent
            # stalling the LLM orchestrator. In a real system we might want to log this.
            await asyncio.wait_for(queue.put(packet), timeout=1.0)

    async def stream_sse(self) -> AsyncGenerator[str, None]:
        """
        Consume the queue and yield strings formatted as SSE.
        Terminates upon encountering a StreamCloseEnvelope.
        """
        queue = await self._get_queue()
        while True:
            packet = await queue.get()

            try:
                # Format as SSE, ensuring multi-line JSON has `data: ` prefix on every line.
                json_str = packet.model_dump_json()
                formatted_data = "\n".join(f"data: {line}" for line in json_str.split("\n"))
                yield f"{formatted_data}\n\n"
            finally:
                queue.task_done()

            if isinstance(packet, StreamCloseEnvelope):
                break
