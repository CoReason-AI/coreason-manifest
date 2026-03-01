import asyncio
from collections.abc import AsyncGenerator

from coreason_manifest.core.telemetry.stream import StreamCloseEnvelope, StreamPacket


class AsyncSSEMultiplexer:
    """
    A thread-safe buffer using asyncio.Queue to handle LLM backpressure
    and multiplex stream packets into Server-Sent Events (SSE).
    """

    def __init__(self) -> None:
        self._queue: asyncio.Queue[StreamPacket] = asyncio.Queue(maxsize=250)

    async def push(self, packet: StreamPacket) -> None:
        """
        Push a stream packet into the buffer.
        """
        await self._queue.put(packet)

    async def stream_sse(self) -> AsyncGenerator[str, None]:
        """
        Consume the queue and yield strings formatted as SSE.
        Terminates upon encountering a StreamCloseEnvelope.
        """
        while True:
            packet = await self._queue.get()

            # Use model_dump_json directly, formatting as SSE
            yield f"data: {packet.model_dump_json()}\n\n"

            self._queue.task_done()

            if isinstance(packet, StreamCloseEnvelope):
                break
